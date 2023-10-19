#!/usr/bin/env python
# --encoding: utf-8--

from tango import DeviceProxy, Database
import numpy as np

from closed_loop_xrr.tango_helpers import get_predictions

from pprint import pprint


tango_path = "id00/mlreflectmodelevaluator/mlreflect"

# configure device ... think about this as something that is persistent
db = Database()

# ~ exp_demo_data = np.loadtxt("some_demo_scan.csv", skiprows=1, delimiter=",")
# ~ db.put_device_property(
# ~ tango_path,
# ~ {
# ~ "exp_x_q_or_tth": "tth",
# ~ "exp_energy_in_keV": 12.0,
# ~ "footprint_beam_width": 0.2,
# ~ "footprint_sample_length": 10.0,
# ~ },
# ~ )


dev = DeviceProxy(tango_path)


exp_demo_data = np.loadtxt("mlreflect_demo_scan.csv", skiprows=1, delimiter=",")
db.put_device_property(
    tango_path,
    {
        "exp_x_q_or_tth": "tth",
        "exp_energy_in_keV": 18.0,
        "footprint_beam_width": 0.072,
        "footprint_sample_length": 10.0,
    },
)

dev.mlreflect_trim_front = 3

print("dev state: ", dev.state())


# envisioned usage
# 1 PUSH DATA TO TANGO DEVICE
dev.input_tth = exp_demo_data[:, 0] * 2.0
dev.input_transm = exp_demo_data[:, 4]
dev.input_refl = exp_demo_data[:, 5]
dev.input_count_time = exp_demo_data[:, 2]

# 1b mlreflect specific settings
dev.mlreflect_optimize_q = False
dev.mlreflect_polish = False

# ~ print(dev.get_attribute_list())

# 2 Preprocess and RUN PREDICTION
dev.predict()

# 3 RETRIVE RESULTS
prediction = get_predictions(dev)

pprint(prediction)
