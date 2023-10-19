import time

offset_gam = 0.005
offset_chi = 0.0025
integration_time = 0.5
start_time = time.perf_counter()
fshutopen();autof_eh1.a2scan(chi,0.025,0.025+0.005*255,gam,0.05,2*(0.025+0.005*255),255,0.5)
fshutclose()
stop_time = time.perf_counter()
print(f'the scan took {stop_time-start_time} seconds')
