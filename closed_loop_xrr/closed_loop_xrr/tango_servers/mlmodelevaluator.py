# model evaluator

# --encoding: utf-8--
from collections.abc import Iterable

from tango.server import Device, PipeWriteType
from tango.server import attribute, command, device_property, pipe
from tango import AttrWriteType, AttrQuality, CmdArgType, DevState
from tango.server import run

from ..utils.transform import angle_to_q, energy_to_wavelength
from ..mlreflect.scans import ReflectivityScan

import numpy as np

"""
 Tango device server to wrap around py-torch ML-model
"""


class MLModelEvaluator(Device):

    N_MAX_X = 4096
    N_MAX_Y = 2

    # device properties
    exp_x_q_or_tth = device_property(dtype=str, default_value="q")
    exp_energy_in_keV = device_property(dtype=float, default_value=0.0)
    dataset_identifier = device_property(dtype=str, default_value="0")

    footprint_beam_width = device_property(dtype=float, default_value=None)
    footprint_sample_length = device_property(dtype=float, default_value=None)
    footprint_beam_shape = device_property(dtype=str, default_value="gauss")

    normalize_to = device_property(dtype=str, default_value="max")

    # ~ exp_x_q_or_tth = attribute(
    # ~ dtype=str,
    # ~ fget="read_q_or_tth",
    # ~ fset="write_q_or_tth",
    # ~ access=AttrWriteType.READ_WRITE,
    # ~ )

    input_attributes = {
        "q": [np.float64],
        "refl": [np.float64],
        "corrected_intensity": [np.float64],
        "tth": [np.float64],
        "transm": [np.float64],
        "count_time": [np.float64],
    }
    prediction_attributes = {
        "q": [np.float64],
        "refl": [np.float64],
        "sld": [[np.float64]],
        "parameters": [np.float64],
        "parameter_names": [str],
        "parameters_imag": [np.float64],
    }

    def __init__(self, *args, **kwargs):
        Device.__init__(self, *args, **kwargs)
        self.set_state(DevState.INIT)

        assert (not self.exp_energy_in_keV == 0.0) or self.exp_x_q_or_tth == "q"

        self._prefix_dict = dict()

        self._input_data = self._initialize_dynamic_attributes(
            "input", self.input_attributes
        )
        self._prediction_output = self._initialize_dynamic_attributes(
            "prediction", self.prediction_attributes
        )

    @property
    def prediction_output(self):
        return self._prediction_output

    @property
    def input_data(self):
        return self._input_data

    @command()
    def prepare_data(self):
        # proper failure management via tango status

        # ~ if self.exp_x_q_or_tth == "tth":
        # ~ self._input_data["q"] = angle_to_q(
        # ~ self._input_data["tth"],
        # ~ energy_to_wavelength(self.exp_energy_in_keV * 1000),
        # ~ )

        tmp = None
        if len(self._input_data["count_time"]) == len(self._input_data["tth"]):
            tmp = self._input_data["refl"] / self._input_data["count_time"]
        else:
            tmp = self._input_data["refl"]

        if len(self._input_data["transm"]) == len(self._input_data["tth"]):
            tmp = tmp / self._input_data["transm"]

        scan = ReflectivityScan(
            scan_number=0,
            scattering_angle=self._input_data["tth"],
            intensity=tmp,
            wavelength=energy_to_wavelength(self.exp_energy_in_keV * 1000),
            beam_width=self.footprint_beam_width,
            sample_length=self.footprint_sample_length,
            beam_shape=self.footprint_beam_shape,
            normalize_to=self.normalize_to,
        )

        self._input_data["q"] = scan.q
        self._input_data["corrected_intensity"] = scan.corrected_intensity

        return True

    def _initialize_dynamic_attributes(self, prefix, attributes):

        if prefix in self._prefix_dict:
            att_dict = self._prefix_dict[prefix]
        else:
            att_dict = dict()

        for k, v in attributes.items():
            att_type = None

            if isinstance(v, tuple):
                att_type = v[0]
                att_dict[k] = v[1]
            elif isinstance(v, Iterable):
                att_type = v
                att_dict[k] = []
            else:
                att_type = v
                att_dict[k] = None

            attr = attribute(
                name=prefix + "_" + k,
                dtype=att_type,
                access=AttrWriteType.READ_WRITE,
                fget=self._generic_read,
                fset=self._generic_write,
                max_dim_x=self.N_MAX_X,
                max_dim_y=self.N_MAX_Y,
                # fisallowed=self.generic_is_allowed,
            )
            self.add_attribute(attr)

        self._prefix_dict[prefix] = att_dict
        return self._prefix_dict[prefix]

    def _generic_read(self, attr):
        prefix, name = attr.get_name().split("_", 1)
        value = self._prefix_dict[prefix][name]
        # unlike a normal static attribute read, we have to modify the value
        # inside this attr object, rather than just returning the value
        attr.set_value(value)

    def _generic_write(self, attr):
        prefix, name = attr.get_name().split("_", 1)
        self._prefix_dict[prefix][name] = attr.get_write_value()

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

    @command(dtype_out=str)
    def predict(self):
        raise NotImplementedError
        return "DONE"

    @command(dtype_out=[str])
    def get_ml_attribute_list(self):
        tmp = list()
        for prefix, d in self._prefix_dict.items():
            tmp.extend([f"{prefix}_{k}" for k in d])
        return tmp

    @command(dtype_out=str)
    def q_tth_energy(self):
        return f"exp_x_q_or_tth: '{self.exp_x_q_or_tth}', exp_energy_in_keV:'{self.exp_energy_in_keV}'"


if __name__ == "__main__":
    run((MLModelEvaluator,))
