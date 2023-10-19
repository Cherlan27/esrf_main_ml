from bliss.setup_globals import sy, sz, ct, sleep
from bliss import current_session
from bliss.common.scans.simulation import simu_l2scan  # noqa: F401

from bliss.scanning.group import Sequence
from bliss.scanning.chain import AcquisitionChannel
from bliss.common import tango

#from bliss.scanning.scan_meta import get_user_scan_meta
# todo checkout how to use this ... nxw_scaninfo tests...

sy.custom_set_measured_noise(0.002)
sz.custom_set_measured_noise(0.002)


load_script("xrr_sim.py")  # noqa: F821
xrrsim = XRR_Sim_Diode()

tth = SoftAxis("two-theta", xrrsim)
transm = SoftCounter(xrrsim, "read_transm", name="transm", mode=SamplingMode.SINGLE)
refl = SoftCounter(xrrsim, "read_refl", name="refl", mode=SamplingMode.SINGLE)
frefl = SoftCounter(
    xrrsim, "read_filtered_refl", name="filtered-refl", mode=SamplingMode.SINGLE
)


def scan_and_predict(
    start,
    stop,
    intervalls,
    count_time,
    tango_uri_or_proxy="id00/mlreflectmodelevaluator/mlreflect",
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
        s1 = ascan(tth, start, stop, intervalls, count_time, frefl, transm)
        scan_seq.add(s1)

        ml_device.input_tth = s1.get_data(tth)
        ml_device.input_transm = s1.get_data(transm)
        ml_device.input_refl = s1.get_data(frefl)
        ml_device.input_count_time = [0]

        ml_device.mlreflect_optimize_q = False
        ml_device.mlreflect_polish = False

        ml_device.predict()

        # proper state sync to come...
        sleep(0.5)

        seq.custom_channels["raw_tth"].emit(s1.get_data(tth))
        seq.custom_channels["raw_refl"].emit(s1.get_data(frefl) / s1.get_data(transm))
        seq.custom_channels["raw_q"].emit(ml_device.input_q)
        seq.custom_channels["corr_refl"].emit(ml_device.input_corrected_intensity)
        seq.custom_channels["pred_refl"].emit(ml_device.prediction_refl)
        seq.custom_channels["pred_q"].emit(ml_device.prediction_q)
        seq.custom_channels["params"].emit(ml_device.prediction_parameters)
        seq.custom_channels["params_imag"].emit(ml_device.prediction_parameters_imag)
        seq.custom_channels["params_names"].emit(ml_device.prediction_parameter_names)

    return seq

def scan_and_predict_counter_based(start, stop, intervalls, count_time):
    seq = Sequence()
    with seq.sequence_context() as scan_seq:
        s1 = ascan(tth, start, stop, intervalls, count_time, frefl, transm)
        scan_seq.add(s1)


load_script("demo_session.py")  # noqa: F821
if "SCAN_DISPLAY" in current_session.env_dict:
    current_session.env_dict["SCAN_DISPLAY"].auto = False
