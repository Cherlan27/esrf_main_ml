import time

integration_time = 0.1
start_time = time.perf_counter()
#fshutopen();autof_eh1.a2scan(chi,0.025,0.025+0.005*255,gam,0.05,2*(0.025+0.005*255),255,integration_time)

umv(watt0,6);a2scan(chi,0.05,0.025+0.005*75,gam,0.1,2*(0.025+0.005*75),75,integration_time)
#umv(watt0,3);a2scan(chi,0.4,0.025+0.005*185,gam,0.8,2*(0.025+0.005*185),180,integration_time)

fshutclose()
stop_time = time.perf_counter()
print(f'the scan took {stop_time-start_time} seconds')
