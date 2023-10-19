#make sure you run  user_script_load('/data/visitor/mi1462/id10/20230301/scripts/action_timer.py' before loading this scipt



#for sample position ? mm (4mm spacers from the front of hutch) open is 6 trinamic and closed for 12


import time

from bliss.config.channels import Channel


def grow_and_stop(target, priors = None, use_mlreflect: bool = False,old_timer=None):
    #on start
    #cell open
    #sample shutter closed
    
    print("TARGET in grow_and_stop", target)

    def do_scans(d):
        
        
        fshutopen()
        print("******************************************************************************** current thickness:",d)
        
        if d<4.5 or d>9.5:    
            print("-----------------------------------------------------------------------------scanning 2.2 gam scan")
            umv(watt0,3);f2scan(gam,1.,0.02,chi,0.5,0.01,60,.5,scan_info={"fastfit":{"watt0":autof_eh1.transmission,"xrr_scan_group_first":True}}) 
            s1=f2scan.scan
            #scan_seq.add(f2scan.scan)
        
            
            umv(watt0,2);f2scan(gam,2.22,0.02,chi,1.11,0.01,38,.5,scan_info={"fastfit":{"watt0":autof_eh1.transmission,"xrr_scan_group_last":True}}) 
            #scan_seq.add(f2scan.scan)
            s2=f2scan.scan
       
                
        else:  
            print("-----------------------------------------------------------------------------scanning 1,8 gam scan")     
            umv(watt0,3);f2scan(gam,1.,0.02,chi,0.5,0.01,40,.5,scan_info={"fastfit":{"watt0":autof_eh1.transmission,"xrr_scan_group_first":True}}) 
            s1=f2scan.scan
            #scan_seq.add(f2scan.scan)
            
            
            umv(watt0,2);f2scan(gam,1.82,0.02,chi,0.91,0.01,58,.5,scan_info={"fastfit":{"watt0":autof_eh1.transmission,"xrr_scan_group_last":True}}) 
            #scan_seq.add(f2scan.scan)
            s2=f2scan.scan

        fshutclose()
        return [s1,s2]


#these were the scans for PTCDI growth on Sunday morning
#         umv(watt0,7)
#         autof_eh1.always_back=False
#         s1=autof_eh1.a2scan(chi,0.05,0.55,gam,0.1,1.1,21,.5)
#         s2=autof_eh1.a2scan(chi,0.56,1.5,gam,1.12,3,120,.5)
#         autof_eh1.always_back=True
#         umv(watt0,7)
#         return [s1,s2]
        
        
    s0 = do_scans(target)
    print("#####1")
    p0=predict_and_save(s0,fscan=True, priors = priors)
    thickness0=get_thickness_from_params(p0)  #to be done nicer
    print("#####2..... thickness first scan",thickness0)
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
  #  #trinamic_obj.position=11
    print("##############open shutter####") 
    
    def action():
    
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
        gevent.sleep(10)
        print("################# 5s after trigger!!!")
        gevent.sleep(10)
        print("################# 10s after trigger!!!")
        gevent.sleep(10)
        print("################# 15s after trigger!!!")
        gevent.sleep(10)
        print("################# 20s after trigger!!!")
        gevent.sleep(10)
        wcid10f.set("ao2",5.)
        print("################# 25s  shutter closed!!!")

          
    
    timer=ActionTimer(target,d0=thickness0,t0=scan_epoch0,n_max=4)
    timer.set_action(action)
    
    # ~ if old_timer is not None:
        # ~ timer.add_next(old_timer.d[-2],old_timer.time[-2])
        # ~ timer.add_next(old_timer.d[-1],old_timer.time[-1])
        # ~ timer_old.stop()

    kill_soon = Channel("KILL_AFTER_NEXT_SCAN", default_value=False)
    kill_soon.value=False
    thickness=target
    while(True):
        
        s = do_scans(thickness)
                
        p = predict_and_save(s,fscan=True, priors = priors)
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
    
