from dataclasses import dataclass
import numpy as np

from bliss.scanning.group import Sequence
from bliss.scanning.chain import AcquisitionChannel
from bliss.common import tango
from bliss import setup_globals  # import gam

from bliss.scanning.scan_meta import USER_SCAN_META

if "xrr" not in USER_SCAN_META.categories_names():
    USER_SCAN_META.add_categories({"xrr"})
    USER_SCAN_META.xrr.set("xrr", {"@NX_class": "NXdata"})


@dataclass
class Priors:
    d_top: tuple = (0., 1000.)
    d_sio2: tuple = (8., 12.)

    sigma_top: tuple = (0., 50.)
    sigma_sio2: tuple = (0., 5.,)
    sigma_si: tuple = (0., 2.,)

    rho_top: tuple = (8., 14.)
    rho_sio2: tuple = (17.5, 17.9)
    rho_si: tuple = (19.9, 20.1)

    def to_arr(self):
        return np.array([
            self.d_top,
            self.d_sio2,
            self.sigma_top,
            self.sigma_sio2,
            self.sigma_si,
            self.rho_top,
            self.rho_sio2,
            self.rho_si,
        ])


@dataclass
class PreprocessParams:
    energy_keV: float = 17.
    beam_width: float = 0.03
    sample_length: float = 10.
    # max_angle: float = None


def predict_and_save(
        scan_or_scans,
        priors=None,
        preprocess: PreprocessParams = None,
        tango_uri_or_proxy="//id10tmp0.esrf.fr:10000/id00/torchevaluator/reflectorch",
        #  exp_energy_in_keV= 18.0,
        #  footprint_beam_width= 0.03,
        #  footprint_sample_length= 10.0
):
    TTH = setup_globals.gam
    CROI = 'mpx_cdte_22_eh1:roi_counters:roi2_sum'
    BGROI1 = 'mpx_cdte_22_eh1:roi_counters:roi3_sum'
    BGROI2 = 'mpx_cdte_22_eh1:roi_counters:roi4_sum'
    TRANSM = 'autof_eh1:transm'

    if not isinstance(scan_or_scans, list):
        scans = [scan_or_scans]
    else:
        scans = scan_or_scans
    tth_data = np.array([x.get_data(TTH) for x in scans]).flatten()
    transm_data = np.array([x.get_data(TRANSM) for x in scans]).flatten()
    intens_data = np.array([x.get_data(CROI) - x.get_data(BGROI1) - x.get_data(BGROI2) for x in scans]).flatten()

    return predict_and_save_on_array(tth_data, transm_data, intens_data, scans=scans, priors=priors, preprocess=preprocess,
                              tango_uri_or_proxy=tango_uri_or_proxy)  # ,exp_energy_in_keV=exp_energy_in_keV,footprint_beam_width=footprint_beam_width,footprint_sample_length=footprint_sample_length)


def predict_and_save_from_h5(
        priors=None, preprocess=None, h5obj=None, h5_path: str = None, scan_num: str = None,
        root_path: str = "/home/esrf/Documents/mi1462/raw/",
        angle_key: str = "gam",
        transm_key: str = "autof_eh1_transm",
        intensity_key: str = "mpx_cdte_22_eh1_roi2",
        tango_uri_or_proxy: str = "//id10tmp0.esrf.fr:10000/id00/torchevaluator/reflectorch",

):
    if h5obj is None:
        if (h5_path is None) or (scan_num is None):
            raise ValueError("h5obj is not provided, so the function requires both h5_path and scan_num to open h5.")
        h5obj = setup_globals.h5todict(root_path + h5_path, f"{scan_num}/measurement")

    return predict_and_save_on_array(
        h5obj[angle_key], h5obj[transm_key], h5obj[intensity_key],
        priors=priors,
        preprocess=preprocess,
        tango_uri_or_proxy=tango_uri_or_proxy
    )


def predict_and_save_on_array(
        tth_data, transm_data, intens_data,
        scans=None,
        priors=None,
        preprocess=None,
        tango_uri_or_proxy="//id10tmp0.esrf.fr:10000/id00/torchevaluator/reflectorch",
):
    if isinstance(tango_uri_or_proxy, str):
        ml_device = tango.DeviceProxy(tango_uri_or_proxy)
    else:
        ml_device = tango_uri_or_proxy

    priors = (priors or Priors()).to_arr()
    preprocess = preprocess or PreprocessParams()

    seq = Sequence({"xrr": {"q": ">../measurement/raw_q", ">measured": "../measurement/corrected_intensity",
                            "predicted": ">../measurement/raw_intensity"}})
    seq.add_custom_channel(AcquisitionChannel("raw_tth", float, ()))
    seq.add_custom_channel(AcquisitionChannel("corrected_intensity", float, ()))
    seq.add_custom_channel(AcquisitionChannel("raw_q", float, ()))
    seq.add_custom_channel(AcquisitionChannel("predicted_intensity", float, ()))
    seq.add_custom_channel(AcquisitionChannel("predicted_q", float, ()))
    seq.add_custom_channel(AcquisitionChannel("params", float, ()))
    #    seq.add_custom_channel(AcquisitionChannel("params_imag", float, ()))
    seq.add_custom_channel(AcquisitionChannel("params_names", str, ()))
    seq.add_custom_channel(AcquisitionChannel("polished_intensity", float, ()))
    seq.add_custom_channel(AcquisitionChannel("polished_params", float, ()))
    with seq.sequence_context() as scan_seq:

        if scans is not None:
            for scan in scans:
                scan_seq.add(scan)

        ml_device.input_tth = tth_data
        ml_device.input_transm = transm_data
        ml_device.input_intensity = intens_data
        ml_device.input_count_time = [0]
        ml_device.input_priors = priors

        ml_device.preprocess_beam_width = preprocess.beam_width
        ml_device.preprocess_sample_length = preprocess.sample_length
        ml_device.preprocess_energy_keV = preprocess.energy_keV

        ml_device.predict()

        # proper state sync to come...
        sleep(0.2)

        seq.custom_channels["raw_tth"].emit(tth_data)
        seq.custom_channels["corrected_intensity"].emit(ml_device.prediction_refl)
        seq.custom_channels["raw_q"].emit(ml_device.prediction_q)
        seq.custom_channels["predicted_intensity"].emit(ml_device.prediction_refl_predicted)
        seq.custom_channels["params"].emit(ml_device.prediction_parameters)
        params = ml_device.prediction_parameters
        seq.custom_channels["params_names"].emit(ml_device.prediction_parameter_names)
        param_names = ml_device.prediction_parameter_names
        seq.custom_channels["polished_intensity"].emit(ml_device.prediction_refl_predicted_polished)
        polished_params = ml_device.prediction_parameters_polished
        seq.custom_channels["polished_params"].emit(polished_params)

    return polished_params #should return a named tuple of params param_names polished_params
