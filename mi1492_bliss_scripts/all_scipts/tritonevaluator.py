# model evaluator

# --encoding: utf-8--


from tango.server import Device
from tango.server import attribute, command, device_property
from tango import AttrWriteType, AttrQuality
from tango.server import run

import numpy as np

#from example_model import PreTrainedModel

import tritonclient.http as httpclient
from tritonclient.utils import *
from tritonclient.utils import triton_to_np_dtype

"""
 Tango device server to wrap around py-torch ML-model
"""


class MLModelEvaluator(Device):

  # device properties
  # serial_number = device_property(dtype=str, default_value="USB2+H05208")

  # ~ pretrained_model = attribute(
  # ~ dtype=str,
  # ~ fget="read_filename",
  # ~ fset="write_filename",
  # ~ access=AttrWriteType.READ_WRITE,
  # ~ )

  def __init__(self, *args, **kwargs):
    Device.__init__(self, *args, **kwargs)
    #self._model = PreTrainedModel('awesome_model.pkl')

  # ~ def read_filename(self):
  # ~ print("read_filename")
  # ~ return self._filename

  # ~ def write_filename(self, filename):
  # ~ print("write_filename")
  # ~ self._filename = filename

  # ~ @command(dtype_in=[int])
  # ~ def trigger_n_acquisitions(self, n_sleep):

  # ~ @command(dtype_out=str)
  # ~ def acquistion_state(self):
  # ~ return "Acq. state " + str(self.get_state()) + f" .... current Acq. : {self._i}"

  @command(dtype_in=[np.float32], dtype_out=[np.float32])
  def predict(self, data):
  	data =  dict(np.load('/home/pithan/Documents/closed_loop_beamtime/torch-tango-demo/reflectorch/tests/data/test_preprocessed_curve_1.npz'))
    print(data)
    '''input_data = {
      'intensity': np.zeros(100).astype(np.float32),
      'scattering_angle': np.zeros(100).astype(np.float32),
      'attenuation': np.zeros(100).astype(np.float32),
      'priors': np.zeros(100).astype(np.float32),
      'wavelength': np.zeros(100).astype(np.float32),
      'beam_width': np.zeros(100).astype(np.float32),
      'sample_length': np.zeros(100).astype(np.float32),
    }'''
    

    inputs = []
    for i, key in enumerate(input_data):
      inputs.append(httpclient.InferInput(key, input_data[key].shape, datatype="FP32"))
      inputs[i].set_data_from_numpy(input_data[key])

    inputs.append(httpclient.InferInput("model_name",[1],np_to_triton_dtype(np.object_)))
    inputs[-1].set_data_from_numpy(np.array(['model_l2q64_new_sub_1'], dtype=np.object_))

    client = httpclient.InferenceServerClient(url="localhost:8000")
    outputs = httpclient.InferRequestedOutput("output__0", binary_data=False, class_count=1000)
    
    outputs =[
        httpclient.InferRequestedOutput("q_values"),
        httpclient.InferRequestedOutput("q_interp"),
        httpclient.InferRequestedOutput("parameters"),
        httpclient.InferRequestedOutput("curve"),
        httpclient.InferRequestedOutput("curve_interp")
    ]
    
    
    
    results = client.infer(model_name="dummy_model", inputs=inputs, outputs=outputs)
    print(results.as_numpy("q_values"))
    return results

if __name__ == "__main__":
  run((MLModelEvaluator,))
