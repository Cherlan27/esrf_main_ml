# ML ESRF 


## Installation
- Instance with 128 GB - A40 graphics card necessary (At least 60 Gb necessary)
- install Mambaforge
- install bliss 1.11.x (guided installation) - make_ev
- conda create --name mlreflect --file mlreflect_tango.txt
- apt-cache search supervisor
- apt-get install supervisor
- Create conda environment ("mlreflect")
- Copy old mlreflect and ESRF beamtime code to Documents/ml-ersf via Github (with dependencies)
- pip install -e .
- pip install refl1d
- cd mlreflect-demo
(- start jupyter-lab)
- 

## conda envs
- `bliss_env`: to have beacon to run TangoDB
- `mlreflect`: contains the code for Tensorflow+Tango
- `tango`: to run jive

## access supervisor
to start/stop services go to `http://localhost:9001`

## hostname for access from beamline PCs
visa-vm024.esrf.fr (160.103.214.24)

## configure startup scripts (based on supervisor / esrf bcu can help)
- Tango DB via beacon/bliss
  - `/etc/supervisor/conf.d/beacon.conf`
    `/home/lukas05/Documents/ml-esrf/startup_scripts/beacon.sh`
- mlreflect device server
  - `/etc/supervisor/conf.d/ml_servers.conf`
  - `/home/lukas05/Documents/ml-esrf/startup_scripts/mlreflect-tango-ds.sh`

in case there is trouble with tango properties on the device server, have a look in
`home/lukas05/Documents/ml-esrf/bliss-tango/demo_configuration/tango/ml-mlreflect.yml` (please edit only when beacon is stopped)

## important source files
  - for the Tango Device Server: 
    `/home/lukas05/Documents/ml-esrf/closed_loop_xrr/closed_loop_xrr/tango_servers/mlreflectmodelevaluator.py`
    and
    `/home/lukas05/Documents/ml-esrf/closed_loop_xrr/closed_loop_xrr/mlreflect/tango_fitter.py`
    are what you will need to modify
  - to see how the server is inteded to be used check out `/home/lukas05/Documents/ml-esrf/closed_loop_xrr/demo_clients/mlevaluatorclient.py`s

    ```
    (mlreflect) lukas05@ubuntu:~/Documents/ml-esrf/closed_loop_xrr/demo_clients$ TANGO_HOST=localhost:10000 python mlevaluatorclient.py 
    ```
    in fact, modifying the `mlevaluatorclient.py` to the new usecase is a good startinpoint to before starting to adopt changes in the server

## to inspect and test Tango Server with jive
   ```
   conda activate tango
   TANGO_HOST=localhost:10000 jive
   ```
   Please check Properties in jive `mlreflectmodelevaluator/mlreflect/Properties`


## beamline integration scripts
scrips from the old beamtime are in `mi1492_bliss_scripts`, however they need a lot of cleaning. The most interesting files shoudl be
`ml_beamline_integration_torch.py` and `ml_beamline_integration_torch_mlreflect.py`. Keep in mind when looking at the second one that this was running Tensorflow and Pytorch based codes in two servers in parallel. For this beamtime thinks can be kept simpler!

