import numpy as np
from silx.io.dictdump import h5todict
from dataclasses import dataclass
from ewoksjob.client import submit
from pprint import pprint
from io import BytesIO
import json

def numpy_serialize(a):
    memfile = BytesIO()
    np.save(memfile, a)
    serialized = memfile.getvalue()
    return json.dumps(serialized.decode('latin-1'))



data1 = h5todict("/data/visitor/mi1462/id10/20230301/raw/Alq3_insitu_1/Alq3_insitu_1_run8/Alq3_insitu_1_run8.h5","155.1")
data2 = h5todict("/data/visitor/mi1462/id10/20230301/raw/Alq3_insitu_1/Alq3_insitu_1_run8/Alq3_insitu_1_run8.h5","156.1")
data3 = h5todict("/data/visitor/mi1462/id10/20230301/raw/Alq3_insitu_1/Alq3_insitu_1_run8/Alq3_insitu_1_run8.h5","157.1")


tth = numpy_serialize(np.concatenate((data1["measurement"]['gam'],data2["measurement"]['gam'],data3["measurement"]['gam'])))
intensity = numpy_serialize(np.concatenate((data1["measurement"]['pilatus300k_roi2'],data2["measurement"]['pilatus300k_roi2'],data3["measurement"]['pilatus300k_roi2'])))
transm = numpy_serialize(np.concatenate((np.ones(len(data1["measurement"]['pilatus300k_roi2']))*data1["instrument"]["filtW0"]["transmission"],
np.ones(len(data2["measurement"]['pilatus300k_roi2']))*data2["instrument"]["filtW0"]["transmission"],
np.ones(len(data3["measurement"]['pilatus300k_roi2']))*data3["instrument"]["filtW0"]["transmission"])))

beam_width=numpy_serialize(np.array([.03]))
sample_length=numpy_serialize(np.array([10]))
wavelength=numpy_serialize(np.array([0.7293]))
max_d_change=numpy_serialize(np.array([5]))


@dataclass
class Priors:
    d_top: tuple = (0., 1000.)  #(0., 1000.)
    d_sio2: tuple = (10., 30.)

    sigma_top: tuple = (0., 50.)  #(0., 50.)
    sigma_sio2: tuple = (0., 10.,)
    sigma_si: tuple = (0., 2.,)

    rho_top: tuple = (7., 14.)
    rho_sio2: tuple = (19, 23)
    rho_si: tuple = (19, 21)
    max_d_change: float = 5.
    fit_growth: bool = True

    def to_arr(self):
        return np.array([
            self.d_top,
            self.d_sio2,
            self.sigma_top,
            self.sigma_sio2,
            self.sigma_si,
            self.rho_top,
            self.rho_sio2,
            self.rho_si,
        ])


priors= numpy_serialize(Priors().to_arr())



inputs = [{"task_identifier":"TritonInference","name":"tth","value":tth},
{"task_identifier":"TritonInference","name":"intensity","value":intensity},
{"task_identifier":"TritonInference","name":"transm","value":transm},
{"task_identifier":"TritonInference","name":"beam_width","value":beam_width},
{"task_identifier":"TritonInference","name":"sample_length","value":sample_length},
{"task_identifier":"TritonInference","name":"wavelength","value":wavelength},
{"task_identifier":"TritonInference","name":"max_d_change","value":max_d_change},
{"task_identifier":"TritonInference","name":"priors","value":priors},
]



nodes = [{"id":"triton","task_type":"class","task_identifier":"tasks.TritonInference"}]

workflow = {"graph":{"id":"triton_graph"}, "nodes":nodes}
future = submit(args=(workflow,),kwargs={"inputs":inputs})
pprint(future.get())

