#make sure you run  user_script_load('/data/visitor/mi1462/id10/20230301/scripts/action_timer.py' before loading this scipt



#for sample position ? mm (4mm spacers from the front of hutch) open is 6 trinamic and closed for 12


import time




def grow_and_stop(target, priors = None, use_mlreflect: bool = False):
    #on start
    #cell open
    #sample shutter closed

    def do_scans():
        #offset_gam = 0.005
        #offset_chi = 0.0025
        #attinuator8 = 0.05
        #integration_time = 0.05
        
        #umv(watt0,6);fshutopen();f2scan(gam,0.1-offset_gam,0.01,chi,0.05-offset_chi,0.005,70,integration_time)
        #umv(watt0,3);f2scan(gam,0.8-offset_gam,0.01,chi,0.4-offset_chi,0.005,80,integration_time)
        #umv(watt0,1);f2scan(gam,1.6-offset_gam,0.01,chi,0.8-offset_chi,0.005,80,integration_time)
        #fshutclose();umv(watt0,6)
        
        #return [SCANS[-3],SCANS[-2],SCANS[-1]]
        
        #return autof_eh1.a2scan(chi,0.05,1.5,gam,0.1,3,191,.5)  
        
         umv(watt0,7)
         autof_eh1.always_back=False
         s1=autof_eh1.a2scan(chi,0.05,0.55,gam,0.1,1.1,21,.5)
         s2=autof_eh1.a2scan(chi,0.56,1.5,gam,1.12,3,120,.5)
         autof_eh1.always_back=True
         umv(watt0,7)
         return [s1,s2]
        
        
    s0 = do_scans()
    print("#####1")
    p0=predict_and_save(s0,fscan=False, priors = priors)
    thickness0=get_thickness_from_params(p0)  #to be done nicer
    print("#####2")
    scan_epoch0 = (s0[1].scan_info['end_timestamp']+s0[0].scan_info['start_timestamp'])/2-(s0[1].scan_info['end_timestamp']-s0[0].scan_info['start_timestamp'])/2
    #scan_epoch0 = (s0.scan_info['end_timestamp']+s0.scan_info['start_timestamp'])/2-(s0.scan_info['end_timestamp']-s0.scan_info['start_timestamp'])/2

    
    elog_print(".... open shutter ---- start growing ....")
    
    #close cell shutter
    #wcid10f.set("ao2",5.)
    
    #open sample shutter
    #time.sleep(1)  
    #mv(trinamic,11.5)                # maybe to be changed!
    #time.sleep(20)  
    #wcid10f.set("ao2",0.)
    
    #open sample shutter
    #mv(trinamic,16)
    trinamic_obj.position=1.5
    
    
    def action():
    
        #close sample shutter
        #time.sleep(1)  
        #mv(trinamic,23)
        #time.sleep(20)
        #wcid10f.set("ao2",5.)
        
        #close sample shutter
        ##mv(trinamic,23)
        trinamic_obj.position=10
      #  print("triggerd!!!")
        
          
    
    timer=ActionTimer(target,d0=thickness0,t0=scan_epoch0)
    timer.set_action(action)
  
    
    while(True):
        
        s = do_scans()
        p = predict_and_save(s,fscan=False, priors = priors)
        thickness = get_thickness_from_params(p, use_mlreflect=use_mlreflect)
                
        scan_epoch = (s[1].scan_info['end_timestamp']+s[0].scan_info['start_timestamp'])/2
        #scan_epoch = (s.scan_info['end_timestamp']+s.scan_info['start_timestamp'])/2

        
        print("*" * 100)
        print("thickness:" ,thickness,"epoch: ",scan_epoch )
        
        timer.add_next(thickness, t=scan_epoch)
        print(f"thickness: {thickness:.2f}, target: {target:.2f}" )
        print("parameters", p)
        print("*" * 100)

        if timer.status>4:   
        #if thickness > target:
            #print("########################################################################################################################################################################################################################")
            print(timer.status)
            elog_print(".... shutter closed by ML---- ")
            break
        print("!" * 100)
        print("## do you want to press ctrl-c ?")
        print("!" * 100)
        sleep(3)
        print("##... too late!")
    
    #close sample shutter
    #time.sleep(10)    
    #mv(trinamic,23)
    #time.sleep(10)    
    #trinamic_obj.position=23
    
    return timer
    
