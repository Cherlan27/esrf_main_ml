from dataclasses import dataclass
import numpy as np

from bliss.scanning.group import Sequence
from bliss.scanning.chain import AcquisitionChannel
from bliss.common import tango
from bliss import setup_globals  # import gam
from silx.io.dictdump import h5todict
import gevent

from bliss.scanning.scan_meta import USER_SCAN_META

if "xrr" not in USER_SCAN_META.categories_names():
    USER_SCAN_META.add_categories({"xrr"})
    USER_SCAN_META.xrr.set("xrr", {"@NX_class": "NXprocess"})


@dataclass
class Priors:
    d_top: tuple = (0., 1000.)  #(0., 1000.)
    d_sio2: tuple = (10., 30.)

    sigma_top: tuple = (0., 50.)  #(0., 50.)
    sigma_sio2: tuple = (0., 10.,)
    sigma_si: tuple = (0., 2.,)

    rho_top: tuple = (7., 14.)
    rho_sio2: tuple = (19, 23)
    rho_si: tuple = (19, 21)
    max_d_change: float = 5.
    fit_growth: bool = True

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
    sample_length: float = 9.
    # max_angle: float = None
    
    
    
def get_thickness_from_params(p, use_mlreflect: bool = False):
    if use_mlreflect:
        thickness = p[1]['Film_thickness']
    else:
        thickness = p[0]['d 1']     
    return thickness




def predict_and_save(
        scan_or_scans,
        priors=None,
        preprocess: PreprocessParams = None,
        tango_uri_or_proxy="//id10tmp0.esrf.fr:10000/id00/torchevaluator/reflectorch",
        #  exp_energy_in_keV= 18.0,
        #  footprint_beam_width= 0.03,
        #  footprint_sample_length= 10.0
        fscan=False
):
    TTH = setup_globals.gam
    CROI = 'pilatus300k:roi_counters:roi2_sum'
    BGROI1 = 'pilatus300k:roi_counters:roi3_sum'
    BGROI2 = 'pilatus300k:roi_counters:roi4_sum'
    TRANSM = 'autof_eh1:transm'

    #if priors is None:   #David
    #    priors = Priors()
    if not isinstance(scan_or_scans, list):
        scans = [scan_or_scans]
    else:
        scans = scan_or_scans
    #print(scans)
    #print(type(scans))
    tth_data = np.concatenate(np.array([x.get_data(TTH) for x in scans]))
    if fscan:
        transm_data =  np.concatenate(np.array([np.ones(x.get_data(TTH).shape)*x.scan_info["instrument"]["filtW0"]["transmission"] for x in scans]))
    else:
        transm_data = np.concatenate(np.array([x.get_data(TRANSM) for x in scans]))
    intens_data = np.concatenate(np.array([x.get_data(CROI) - x.get_data(BGROI1) - x.get_data(BGROI2) for x in scans]))

    return predict_and_save_on_array(tth_data, transm_data, intens_data, scans=scans, priors=priors, preprocess=preprocess,
                              tango_uri_or_proxy=tango_uri_or_proxy)  # ,exp_energy_in_keV=exp_energy_in_keV,footprint_beam_width=footprint_beam_width,footprint_sample_length=footprint_sample_length)


def predict_and_save_from_h5(
        priors=None, preprocess=None, h5obj=None, h5_path: str = None, scan_num: str = None,
        root_path: str = "/home/esrf/Documents/mi1462/raw/",
        angle_key: str = "gam",
        transm_key: str = "autof_eh1_transm",
        intensity_key: str = "pilatus300k_roi2",
        tango_uri_or_proxy: str = "//id10tmp0.esrf.fr:10000/id00/torchevaluator/reflectorch",

):
    if h5obj is None:
        if (h5_path is None) or (scan_num is None):
            raise ValueError("h5obj is not provided, so the function requires both h5_path and scan_num to open h5.")
        h5obj = h5todict(root_path + h5_path, f"{scan_num}/measurement")

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
        
    mlreflect_device=tango.DeviceProxy("//id10tmp0.esrf.fr:10000/id00/mlreflectmodelevaluator/mlreflect")

    priors = priors or Priors()
    print('Priors submitted to the model: ')
    print(priors)
    preprocess = preprocess or PreprocessParams()

    ##### predict
    
    
    ml_device.input_tth = tth_data
    ml_device.input_transm = transm_data
    ml_device.input_intensity =np.clip( intens_data,0,np.infty)
    ml_device.input_count_time = [0]
    ml_device.input_priors = priors.to_arr()
    ml_device.postprocess_max_d_change = priors.max_d_change
    ml_device.postprocess_fit_growth = priors.fit_growth

    ml_device.preprocess_beam_width = preprocess.beam_width
    ml_device.preprocess_sample_length = preprocess.sample_length
    ml_device.preprocess_energy_keV = preprocess.energy_keV
    
    
    ### for mlreflect
    mlreflect_device.input_tth = tth_data
    mlreflect_device.input_transm = transm_data
    mlreflect_device.input_refl = np.clip( intens_data,0,np.infty)
    mlreflect_device.input_count_time = [0]
    ml_device.mlreflect_optimize_q = True
    ml_device.mlreflect_polish = True

  #  try:
  #      ml_device.set_timeout_millis(5000)
  #      ml_device.predict()
       # ml_device.command_inout("predict",timeout=10)
        #sleep(5)
  #  except tango.CommunicationFailed:
  #      sleep(3)
    
    # proper state sync to come...
    
    reply_id = ml_device.command_inout_asynch("predict")
    reply_id_mlreflect = mlreflect_device.command_inout_asynch("predict")
    gevent.sleep(4)
    # ~ while True:
        # ~ try:
          # ~ a= ml_device.command_inout_reply(reply_id)
        # ~ except tango.AsynReplyNotArrived:
          # ~ gevent.sleep(0.2)
          # ~ continue
    # ~ while True:
        # ~ try:
          # ~ b= mlreflect_device.command_inout_reply(reply_id_mlreflect)
        # ~ except tango.AsynReplyNotArrived:
          # ~ gevent.sleep(0.2)
          # ~ continue

    polished_params = ml_device.prediction_parameters_polished
    param_names = ml_device.prediction_parameter_names
    
    params_mlreflect = mlreflect_device.prediction_parameters
    param_namess_mlreflect = mlreflect_device.prediction_parameter_names

    info={"xrr":dict(zip(param_names, polished_params)),"mlreflect":dict(zip(param_namess_mlreflect, params_mlreflect))}
    #{"xrr": {"q": ">../measurement/raw_q", ">measured": "../measurement/corrected_intensity",
    #                        "predicted": ">../measurement/raw_intensity"}}

    seq = Sequence(title=f"AI_fit_thickness_{int(polished_params[0])}_Ang",scan_info=info)
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
    
    seq.add_custom_channel(AcquisitionChannel("mlreflect_corrected_intensity", float, ()))
    seq.add_custom_channel(AcquisitionChannel("mlreflect_q", float, ()))
    seq.add_custom_channel(AcquisitionChannel("mlreflect_predicted_intensity", float, ()))
    seq.add_custom_channel(AcquisitionChannel("mlreflect_params", float, ()))
    seq.add_custom_channel(AcquisitionChannel("mlreflect_params_names", str, ()))
    
    with seq.sequence_context() as scan_seq:

        if scans is not None:
            for scan in scans:
                scan_seq.add(scan)

        seq.custom_channels["raw_tth"].emit(tth_data)
        seq.custom_channels["corrected_intensity"].emit(ml_device.prediction_refl)
        seq.custom_channels["raw_q"].emit(ml_device.prediction_q)
        seq.custom_channels["predicted_intensity"].emit(ml_device.prediction_refl_predicted)
        seq.custom_channels["params"].emit(ml_device.prediction_parameters)
        params = ml_device.prediction_parameters
        seq.custom_channels["params_names"].emit(ml_device.prediction_parameter_names)
        seq.custom_channels["polished_intensity"].emit(ml_device.prediction_refl_predicted_polished)
        seq.custom_channels["polished_params"].emit(polished_params)
        
        seq.custom_channels["mlreflect_corrected_intensity"].emit(mlreflect_device.input_corrected_intensity)
        seq.custom_channels["mlreflect_q"].emit(mlreflect_device.prediction_q)
        seq.custom_channels["mlreflect_predicted_intensity"].emit(mlreflect_device.prediction_refl)
        seq.custom_channels["mlreflect_params"].emit(mlreflect_device.prediction_parameters)
        seq.custom_channels["mlreflect_params_names"].emit(mlreflect_device.prediction_parameter_names)

    return dict(zip(param_names, polished_params)),dict(zip(param_namess_mlreflect, params_mlreflect))
    
    #polished_params,params_mlreflect #should return a named tuple of params param_names polished_params
