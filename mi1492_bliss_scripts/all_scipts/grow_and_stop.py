#make sure you run  user_script_load('/data/visitor/mi1462/id10/20230301/scripts/action_timer.py' before loading this scipt



def grow_and_stop(target):
    #on start
    #cell open
    #sample shutter closed
    
    s0=autof_eh1.a2scan(chi,0.025,0.025+0.005*255,gam,0.05,2*(0.025+0.005*255),127,.5)
    p0=predict_and_save(s0,priors=priors)
    thickness0=p0[0]  #to be done nicer
    scan_epoch0 = (s0.scan_info['end_timestamp']+s0.scan_info['start_timestamp'])/2-(s0.scan_info['end_timestamp']-s0.scan_info['start_timestamp'])/2
    
    elog_print(".... open shutter ---- start growing ....")
    
    #close cell shutter
    wcid10f.set("ao2",5.)
    
    #open sample shutter
    #mv(trinamic,15.5)
    
    wcid10f.set("ao2",0.)
    
    def action():
        #close cell shutter
        wcid10f.set("ao2",0.)
    
        #open sample shutter
        #mv(trinamic,23)
    
    timer=ActionTimer(target,d0=thickness0,t0=scan_epoch0)
    timer.set_action(action)
    
    
    while(True):
        
        s=autof_eh1.a2scan(chi,0.025,0.025+0.005*255,gam,0.05,2*(0.025+0.005*255),127,.5)
        p=predict_and_save(s,priors=priors)
        
        thickness=p[0]  #to be done nicer
        scan_epoch = (s.scan_info['end_timestamp']+s.scan_info['start_timestamp'])/2
        
        print("thickness:" ,thickness,"epoch: ",scan_epoch )
        
        timer.add_next(thickness, t=scan_epoch)
        
        if timer.status>4:
            elog_print(".... shutter closed by ML---- ")
            break
    
    return timer
    
