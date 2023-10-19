from bliss.common.counter import SamplingMode, SoftCounter
from bliss.common.soft_axis import SoftAxis

import numpy as np
from scipy import interpolate

from bliss.scanning.group import Sequence
from bliss.scanning.chain import AcquisitionChannel
from bliss.common import tango


class XRR_Sim_Diode:
    """To be used in ascan as SoftAxis and SoftCounter at the same time"""

    def __init__(self):
        # abs pass definetly not good coding style, could/should be fixed later...
        exp_demo_data = np.loadtxt(
            "/data/visitor/mi1462/id10/20230301/scripts/mlreflect_demo_scan.csv",
            skiprows=1,
            delimiter=",",
        )
        self._tth = exp_demo_data[:, 0] * 2.0
        self._transm = exp_demo_data[:, 4]
        self._f_transm = interpolate.interp1d(self._tth, self._transm)
        self._refl = np.log10(exp_demo_data[:, 5] / self._transm)
        self._f_refl = interpolate.interp1d(
            self._tth, np.log10(exp_demo_data[:, 5] / self._transm)
        )

        self.pos = np.min(self._tth)
        print(f"tth min:{np.min(self._tth)}, tth max:{np.max(self._tth)}")

    # ~ def _interp_reflectivity(self, q_interp, q, reflectivity):
    # ~ """Interpolate data on a base10 logarithmic scale."""
    # ~ return 10 ** np.interp(q_interp, q, np.log10(reflectivity))

    def read_transm(self):
        return self._f_transm(self.pos)

    def read_refl(self):
        return 10 ** self._f_refl(self.pos)

    def read_filtered_refl(self):
        return self.read_refl() * self.read_transm()

    @property
    def position(self):
        return self.pos

    @position.setter
    def position(self, val):
        self.pos = val
        
xrrsim = XRR_Sim_Diode()

sim_tth = SoftAxis("two-theta", xrrsim)
sim_transm = SoftCounter(xrrsim, "read_transm", name="transm", mode=SamplingMode.SINGLE)
sim_refl = SoftCounter(xrrsim, "read_refl", name="refl", mode=SamplingMode.SINGLE)
sim_frefl = SoftCounter(
    xrrsim, "read_filtered_refl", name="filtered-refl", mode=SamplingMode.SINGLE
)


def scan_and_predict(
    start,
    stop,
    intervalls,
    count_time,
    tango_uri_or_proxy="//id10tmp0.esrf.fr:10000/id00/mlreflectmodelevaluator/mlreflect",
):

    if isinstance(tango_uri_or_proxy, str):
        ml_device = tango.DeviceProxy(tango_uri_or_proxy)
    else:
        ml_device = tango_uri_or_proxy

    seq = Sequence()
    seq.add_custom_channel(AcquisitionChannel("raw_tth", float, ()))
    seq.add_custom_channel(AcquisitionChannel("raw_refl", float, ()))
    seq.add_custom_channel(AcquisitionChannel("raw_q", float, ()))
    seq.add_custom_channel(AcquisitionChannel("corr_refl", float, ()))
    seq.add_custom_channel(AcquisitionChannel("pred_refl", float, ()))
    seq.add_custom_channel(AcquisitionChannel("pred_q", float, ()))
    seq.add_custom_channel(AcquisitionChannel("params", float, ()))
    seq.add_custom_channel(AcquisitionChannel("params_imag", float, ()))
    seq.add_custom_channel(AcquisitionChannel("params_names", str, ()))

    with seq.sequence_context() as scan_seq:
        s1 = ascan(sim_tth, start, stop, intervalls, count_time, sim_frefl, sim_transm)
        scan_seq.add(s1)

        ml_device.input_tth = s1.get_data(sim_tth)
        ml_device.input_transm = s1.get_data(sim_transm)
        ml_device.input_refl = s1.get_data(sim_frefl)
        ml_device.input_count_time = [0]

        ml_device.mlreflect_optimize_q = False
        ml_device.mlreflect_polish = False

        ml_device.predict()

        # proper state sync to come...
        sleep(0.5)

        seq.custom_channels["raw_tth"].emit(s1.get_data(sim_tth))
        seq.custom_channels["raw_refl"].emit(s1.get_data(sim_frefl) / s1.get_data(sim_transm))
        seq.custom_channels["raw_q"].emit(ml_device.input_q)
        seq.custom_channels["corr_refl"].emit(ml_device.input_corrected_intensity)
        seq.custom_channels["pred_refl"].emit(ml_device.prediction_refl)
        seq.custom_channels["pred_q"].emit(ml_device.prediction_q)
        seq.custom_channels["params"].emit(ml_device.prediction_parameters)
        seq.custom_channels["params_imag"].emit(ml_device.prediction_parameters_imag)
        seq.custom_channels["params_names"].emit(ml_device.prediction_parameter_names)

    return seq

