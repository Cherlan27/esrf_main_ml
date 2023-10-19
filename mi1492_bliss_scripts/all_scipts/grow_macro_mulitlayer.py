from bliss.scanning.group import Sequence
import numpy as np
import gevent


def pulse():
    
        #close sample shutter
        #time.sleep(1)  
        #mv(trinamic,23)
        #time.sleep(20)
        #wcid10f.set("ao2",5.)
        
        #close sample shutter
        ##mv(trinamic,23)
   #     trinamic_obj.position=17
        print("#################3 triggerd!!!")
        wcid10f.set("ao2",0.)
        gevent.sleep(5)
        print("################# 5s after trigger!!!")
        gevent.sleep(5)
        print("################# 10s after trigger!!!")
        gevent.sleep(5)
        print("################# 15s after trigger!!!")
        gevent.sleep(5)
        wcid10f.set("ao2",5.)
        print("################# 20s  shutter closed!!!")


def growth_macro(
    #if there is already some film on top you can start from this number times the step size
    step_num: int = 1, 
    thickness_step: int = 1.0, 
    num_steps: int = 20,
    fit_growth: bool = True,
    max_d_change: float = 5.,
    min_rel_bound: float = 2.,
    use_mlreflect: bool = False,
    pulse_at_start: bool = False
):
    global TIMER_GREENLET
    offset_gam = 0.005
    offset_chi = 0.0025

    #umv(watt0,7)
    

    target_thickness_array = []
    thickness_array = []
    timer=None
    try:
        for i in range(step_num, num_steps):
            
            target_thickness = thickness_step * i
            target_thickness_array.append(target_thickness)

            priors = Priors(
            d_top=(max(0, (i-min_rel_bound) * thickness_step), (2*i)*thickness_step), 
            d_sio2=(10.0, 30.0), 
            sigma_top=(0.0, 50.0),
            sigma_sio2=(0.0, 10.0), 
            sigma_si=(0.0, 2.0), 
            rho_top=(7.0, 14.0), 
            rho_sio2=(20, 24), 
            rho_si=(19, 22.5),
            )
            
            print("*" * 100)
            print(
            f"Starting new growth step {i} with target thickness {target_thickness}, d_top = ({priors.d_top[0]:.2f}, {priors.d_top[1]:.2f})"
            )
            print("*" * 100)
            
            timer=grow_and_stop(target_thickness, priors=priors, use_mlreflect=use_mlreflect,old_timer=timer)
            
            umv(watt0,6);fshutopen();f2scan(gam,0.1-offset_gam,0.01,chi,0.05-offset_chi,0.005,70,.5)
            #umv(watt0,3);f2scan(gam,0.8-offset_gam,0.01,chi,0.4-offset_chi,0.005,80,.5)
            #umv(watt0,1);f2scan(gam,1.6-offset_gam,0.01,chi,0.8-offset_chi,0.005,80,.5)
            fshutclose();umv(watt0,6);
            
           # s=autof_eh1.a2scan(chi,0.05,1.5,gam,0.1,3,255,.5)  
            
            priors.fit_growth = False
            
            #p = predict_and_save(s,fscan=False, priors=priors)
            
            #s=autof_eh1.a2scan(chi,0.025,0.025+0.005*255,gam,0.05,2*(0.025+0.005*255),127,.5)
            #p=predict_and_save(s, priors = priors)

            #thickness = get_thickness_from_params(p, use_mlreflect=use_mlreflect)
            #thickness_array.append(thickness)
            
            #print("*" * 100)
            #print(f"next target thickness:{target_thickness} reached thickness:{thickness}")
            #print("*" * 100)
        
    finally:
        
        seq = Sequence(title=f"AI ramp")
        seq.add_custom_channel(AcquisitionChannel("target", float, ()))
        seq.add_custom_channel(AcquisitionChannel("reached_value", float, ()))
        with seq.sequence_context() as scan_seq:

                seq.custom_channels["target"].emit(np.array(target_thickness_array))
                seq.custom_channels["reached_value"].emit(np.array(thickness_array))
            
        #cleanup
        gevent.killall(TIMER_GREENLET)
        TIMER_GREENLET=[]
        autof_eh1.always_back=True
        umv(watt0,7)
