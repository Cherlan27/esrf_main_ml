
from bliss.scanning.group import Group
from bliss.config.channels import Channel
import gevent

from dataclasses import dataclass
import numpy as np
from bliss.scanning.chain import AcquisitionChannel

from bliss.common import tango

@dataclass
class PreprocessParams:
    energy_keV: float = 17.
    beam_width: float = 0.03
    sample_length: float = 9.
    # max_angle: float = None
    
    

def run_synchron_loop(d0=0, total_count=7.96155e11):
    kill_soon = Channel("KILL_AFTER_NEXT_SCAN", default_value=False)
    kill_soon.value=False
    d=d0
    try:
        while (True):
           # seq = Sequence(title=f"xrr loop")
            #with seq.sequence_context() as scan_seq:
                fshutopen()
                print("******************************************************************************** current thickness:",d)
                
                if d<4.5 or d>9.5:    
                    print("-----------------------------------------------------------------------------scanning 2.2 gam scan")
                    umv(watt0,3);f2scan(gam,1.,0.02,chi,0.5,0.01,60,.5,scan_info={"fastfit":{"watt0":autof_eh1.transmission,"xrr_scan_group_first":True}}) 
                    s1=f2scan.scan
                    #scan_seq.add(f2scan.scan)
                    if kill_soon.value:
                        break
                    
                    umv(watt0,2);f2scan(gam,2.22,0.02,chi,1.11,0.01,38,.5,scan_info={"fastfit":{"watt0":autof_eh1.transmission,"xrr_scan_group_last":True}}) 
                    #scan_seq.add(f2scan.scan)
                    s2=f2scan.scan
                    if kill_soon.value:
                        break
                        
                else:  
                    print("-----------------------------------------------------------------------------scanning 1,8 gam scan")     
                    umv(watt0,3);f2scan(gam,1.,0.02,chi,0.5,0.01,40,.5,scan_info={"fastfit":{"watt0":autof_eh1.transmission,"xrr_scan_group_first":True}}) 
                    s1=f2scan.scan
                    #scan_seq.add(f2scan.scan)
                    if kill_soon.value:
                        break
                    
                    umv(watt0,2);f2scan(gam,1.82,0.02,chi,0.91,0.01,58,.5,scan_info={"fastfit":{"watt0":autof_eh1.transmission,"xrr_scan_group_last":True}}) 
                    #scan_seq.add(f2scan.scan)
                    s2=f2scan.scan
                    if kill_soon.value:
                        break    
                    
                    
                    
                    
                
                tango_uri_or_proxy="//id10tmp0.esrf.fr:10000/id00/multilayerevaluator/multilayer"
                ml_device = tango.DeviceProxy(tango_uri_or_proxy)
                
                
                TTH = setup_globals.gam
                CROI = 'pilatus300k:roi_counters:roi2_sum'
                BGROI1 = 'pilatus300k:roi_counters:roi3_sum'
                BGROI2 = 'pilatus300k:roi_counters:roi4_sum'
                TRANSM = 'autof_eh1:transm'

                #if priors is None:   #David
                #    priors = Priors()
               # if not isinstance(scan_or_scans, list):
               #     scans = [scan_or_scans]
               # else:
                #    scans = scan_or_scans
                #print(scans)
                #print(type(scans))
                
                scans=[s1,s2]
                
                tth_data = np.concatenate(np.array([x.get_data(TTH) for x in scans]))
             #   if fscan:
                transm_data =  np.concatenate(np.array([np.ones(x.get_data(TTH).shape)*x.scan_info["instrument"]["filtW0"]["transmission"] for x in scans]))
           #     else:
            #        transm_data = np.concatenate(np.array([x.get_data(TRANSM) for x in scans]))
                intens_data = np.concatenate(np.array([x.get_data(CROI) - x.get_data(BGROI1) - x.get_data(BGROI2) for x in scans]))


                #print("tth",tth_data)
                #print("transm_data",transm_data)
                #print("intens_data",intens_data)

                preprocess = PreprocessParams()

                
                ml_device.input_tth = tth_data
                ml_device.input_transm = transm_data
                ml_device.input_intensity =np.clip( intens_data,0,np.infty)
                ml_device.input_count_time = [0]

                ml_device.preprocess_beam_width = preprocess.beam_width
                ml_device.preprocess_sample_length = preprocess.sample_length
                ml_device.preprocess_energy_keV = preprocess.energy_keV
                ml_device.preprocess_incoming_intensity = total_count
                
                ml_device.set_timeout_millis(60000)
                ml_device.predict()
                
                fshutclose()
                
                polished_params = ml_device.prediction_parameters_polished
                param_names = ml_device.prediction_parameter_names

                info={"xrr":dict(zip(param_names, polished_params))}
                
                seq = Sequence(title=f"AI_fit_thickness_{polished_params[0]:.3f} Monolayer",scan_info=info)
                seq.add_custom_channel(AcquisitionChannel("raw_tth", float, ()))
                seq.add_custom_channel(AcquisitionChannel("corrected_intensity", float, ()))
                seq.add_custom_channel(AcquisitionChannel("raw_q", float, ()))
                seq.add_custom_channel(AcquisitionChannel("predicted_intensity", float, ()))
                seq.add_custom_channel(AcquisitionChannel("predicted_q", float, ()))
                seq.add_custom_channel(AcquisitionChannel("params", float, ()))
                seq.add_custom_channel(AcquisitionChannel("params_names", str, ()))
                seq.add_custom_channel(AcquisitionChannel("polished_intensity", float, ()))
                seq.add_custom_channel(AcquisitionChannel("polished_params", float, ()))
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

                d= polished_params[0]
                
                print("PREDICTED_THICKNESS",d)
                
                if kill_soon.value:
                    break
            
    finally:
        fshutclose()
        mv(watt0,7)


