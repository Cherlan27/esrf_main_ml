import time


offset_gam = 0.005
offset_chi = 0.0025
attinuator8 = 0.05
integration_time = 0.1
start_time = time.perf_counter()


umv(watt0,9)
#nice scan
#umv(watt0,6);fshutopen();f2scan(gam,0.1-offset_gam,0.01,chi,0.05-offset_chi,0.005,40,integration_time)
#umv(watt0,4);f2scan(gam,0.5-offset_gam,0.01,chi,0.25-offset_chi,0.005,30,integration_time)
#umv(watt0,3);f2scan(gam,0.8-offset_gam,0.01,chi,0.4-offset_chi,0.005,160,integration_time)

#fast scan
umv(watt0,6);fshutopen();f2scan(gam,0.1-offset_gam,0.01,chi,0.05-offset_chi,0.005,70,integration_time)
umv(watt0,3);f2scan(gam,0.8-offset_gam,0.01,chi,0.4-offset_chi,0.005,80,integration_time)
umv(watt0,1);f2scan(gam,1.6-offset_gam,0.01,chi,0.8-offset_chi,0.005,80,integration_time)


priors = Priors(d_top=(0.0, 80.0), d_sio2=(10.0, 30.0), sigma_top=(0.0, 50.0), sigma_sio2=(0.0, 10.0), sigma_si=(0.0, 2.0), rho_top=(7.0, 14.0), rho_sio2=(19, 23), rho_si=(19, 21))
p=predict_and_save([SCANS[-3],SCANS[-2],SCANS[-1]],fscan=True, priors = priors)
#thickness=p[0]  #to be done nicer    (900,1000),(10,30),(0,50),(0,10),(0,2),(7,14),(19,23),(19,21)
#print("thickness:" ,thickness)



#umv(watt0,8);fshutopen();f2scan(gam,0.1-offset_gam,0.01,chi,0.05-offset_chi,0.005,16,integration_time) 
#umv(watt0,7);f2scan(gam,0.21-offset_gam,0.01,chi,0.105-offset_chi,0.005,8,integration_time)
#umv(watt0,6);f2scan(gam,0.29-offset_gam,0.01,chi,0.145-offset_chi,0.005,8,integration_time)
#umv(watt0,5);f2scan(gam,0.37-offset_gam,0.01,chi,0.185-offset_chi,0.005,22,integration_time)
#umv(watt0,4);f2scan(gam,0.59-offset_gam,0.01,chi,0.295-offset_chi,0.005,45,integration_time)
#umv(watt0,3);f2scan(gam,1.04-offset_gam,0.01,chi,0.52-offset_chi,0.005,91,integration_time)
#umv(watt0,2);f2scan(gam,1.95-offset_gam,0.01,chi,0.975-offset_chi,0.005,65,integration_time);fshutclose();umv(watt0,9);


#f2scan(gam,2*(0.025+0.005*255),-0.01,chi,0.025+0.005*255,-0.005,255,integration_time) #


fshutclose();umv(watt0,9);
stop_time = time.perf_counter()
print(f'the scan took {stop_time-start_time} seconds')

