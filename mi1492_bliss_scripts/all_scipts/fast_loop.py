
from bliss.scanning.group import Group
from bliss.config.channels import Channel
import gevent


def run_fast_loop(i0=0):
    kill_soon = Channel("KILL_AFTER_NEXT_SCAN", default_value=False)
    kill_soon.value=False
    try:
        i=i0
        while (True):
           # seq = Sequence(title=f"xrr loop")
            #with seq.sequence_context() as scan_seq:
                fshutopen()
                
                umv(watt0,3);f2scan(gam,1.,0.02,chi,0.5,0.01,6,.5,scan_info={"fastfit":{"watt0":autof_eh1.transmission,"xrr_scan_group_first":True}}) #60
                s1=f2scan.scan
                #scan_seq.add(f2scan.scan)
                if kill_soon.value:
                    break
                
                umv(watt0,1);f2scan(gam,2.22,0.02,chi,1.11,0.01,3,.5,scan_info={"fastfit":{"watt0":autof_eh1.transmission,"xrr_scan_group_last":True}}) #38
                #scan_seq.add(f2scan.scan)
                s2=f2scan.scan
                if kill_soon.value:
                    break
                
                i=i+1
                Group(s1,s2)
                
                
                fshutclose()
                gevent.sleep(10)
            
    finally:
        fshutclose()
        mv(watt0,7)
