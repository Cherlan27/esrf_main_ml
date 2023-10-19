#!/usr/bin/env python
# --encoding: utf-8--

# start using TANGO_HOST=localhost:10000 python -u -m closed_loop_xrr.tango_servers.mlreflectmodelevaluator mlreflect


from tango.server import Device
from tango.server import attribute, command, device_property
from tango import AttrWriteType, AttrQuality, DevState
from tango.server import run

import numpy as np

from .mlmodelevaluator import MLModelEvaluator
from ..mlreflect.tango_fitter import DefaultTangoFitter

from ..utils.transform import angle_to_q, energy_to_wavelength


"""
 Tango device server to wrap around mlreflect
"""


class MLReflectModelEvaluator(MLModelEvaluator):

    mlreflect_attributes = {
        "trim_front": (int, 0),
        "trim_back": (int, 0),
        "theta_offset": (float, 0.0),
        "dq": (float, 0.0),
        "factor": (float, 1.0),
        "polish": (bool, True),
        "fraction_bounds": ([float], np.array([0.5, 0.5, 0.1])),
        "optimize_q": (bool, True),
        "n_q_samples": (int, 1000),
        "optimize_scaling": (bool, False),
        "n_scale_samples": (int, 300),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._mlreflect = self._initialize_dynamic_attributes(
            "mlreflect", self.mlreflect_attributes
        )

        self._fitter = DefaultTangoFitter()

        self.set_state(DevState.STANDBY)

    @property
    def mlreflect(self):
        return self._mlreflect

    @command(dtype_out=str)
    def predict(self):
        self.set_state(DevState.RUNNING)

        self.prepare_data()

        params = {
            "wavelength": energy_to_wavelength(self.exp_energy_in_keV * 1000),
            "beam_width": self.footprint_beam_width,
            "sample_length": self.footprint_sample_length,
            "beam_shape": self.footprint_beam_shape,
            "normalize_to": self.normalize_to,
        }
        self._fitter._footprint_params.update(params)

        (
            identifier,
            predicted_parameters,
            predicted_refl,
            q_values_prediction,
            fit_result,
        ) = self._fitter.fit(
            self._input_data["corrected_intensity"],
            self._input_data["q"],
            trim_front=(
                None
                if self.mlreflect["trim_front"] == 0
                else self.mlreflect["trim_front"]
            ),
            trim_back=(
                None
                if self.mlreflect["trim_back"] == 0
                else self.mlreflect["trim_back"]
            ),
            theta_offset=self.mlreflect["theta_offset"],
            dq=self.mlreflect["dq"],
            factor=self.mlreflect["factor"],
            polish=self.mlreflect["polish"],
            fraction_bounds=tuple(self.mlreflect["fraction_bounds"]),
            optimize_q=self.mlreflect["optimize_q"],
            n_q_samples=self.mlreflect["n_q_samples"],
            optimize_scaling=self.mlreflect["optimize_scaling"],
            n_scale_samples=self.mlreflect["n_scale_samples"],
        )

        print(predicted_parameters)

        # ~ prediction_attributes = {
        # ~ "q": [np.float64],
        # ~ "refl": [np.float64],
        # ~ "sld": [np.float64],
        # ~ "parameters":[np.float64],
        # ~ "parameter_names":[str],
        # ~ "parameters_imag":[np.float64],
        # ~ }
        self.prediction_output["q"] = q_values_prediction
        self.prediction_output["refl"] = predicted_refl.flatten()
        self.prediction_output["parameter_names"] = list(predicted_parameters)
        self.prediction_output["parameters"] = np.real(
            np.array(predicted_parameters)
        ).flatten()
        self.prediction_output["parameters_imag"] = np.imag(
            np.array(predicted_parameters)
        ).flatten()

        # now we deal with sld

        self.prediction_output["sld"] = fit_result.sld_profile

        self.set_state(DevState.STANDBY)

        return "PREDICTION DONE"


if __name__ == "__main__":
    run((MLReflectModelEvaluator,))
