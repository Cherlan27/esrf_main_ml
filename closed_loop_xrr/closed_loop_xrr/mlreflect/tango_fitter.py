from typing import Iterable

import numpy as np

from mlreflect.curve_fitter.base_fitter import BaseFitter
from .results import FitResult, FitResultSeries
from mlreflect.models import DefaultTrainedModel

# from ..xrrloader import SpecLoader

from pprint import pprint


class TangoFitter(BaseFitter):
    """Takes reflectivity scan via Tango and fits it using a trained neural network model.

    Before use:
        - A neural network model has to be set via the ``set_trained_model()`` method.
        - Import parameters have to be defined via the ``set_import_params()`` method.
        - Parameters for footprint correction have to be defined via ``set_footprint_params()`` method.
        - The input SPEC file has to be specified via the ``set_spec_file()`` method.
    """

    def fit(
        self,
        corrected_intensity: np.array,
        q_values: np.array,
        trim_front: int = None,
        trim_back: int = None,
        theta_offset: float = 0.0,
        dq: float = 0.0,
        factor: float = 1.0,
        plot=False,
        polish=True,
        fraction_bounds: tuple = (0.5, 0.5, 0.1),
        optimize_q=True,
        n_q_samples: int = 1000,
        optimize_scaling=False,
        n_scale_samples: int = 300,
        identifier: str = "",
    ) -> tuple:

        """predict thin film parameters.

        Args:
            exp_q: array of experimental q_values
            exp_refl: array of exp. reflectivity values
            trim_front: How many intensity points are cropped from the beginning.
            trim_back: How many intensity points are cropped from the end.
            theta_offset: Angular correction that is added before transformation to q space.
            dq: Q-shift that is applied before interpolation of the data to the trained q values. Can sometimes
                improve the results if the total reflection edge is not perfectly aligned.
            factor: Multiplicative factor that is applied to the data after interpolation. Can sometimes
                improve the results if the total reflection edge is not perfectly aligned.
            plot: If set to ``True``, the intensity prediction is shown in a plot.
            polish: If ``True``, the predictions will be refined with a simple least log mean squares minimization via
                ``scipy.optimize.minimize``. This can often improve the "fit" of the model curve to the data at the
                expense of higher prediction times.
            fraction_bounds: The relative fitting bounds if the LMS for thickness, roughness and SLD, respectively.
                E.g. if the predicted thickness was 150 A, then a value of 0.5 would mean the fit bounds are
                ``(75, 225)``.
            optimize_q: If ``True``, the q interpolation will be resampled with small q shifts in a range of about
                +-0.003 1/A and the neural network prediction with the smallest MSE will be selected. If
                ``polish=True``, this step will happen before the LMS fit.
            n_q_samples: Number of q shift samples that will be generated. More samples can lead to a better result,
                but will increase the prediction time.
            optimize_scaling: If ``True``, the interpolated input curve is randomly rescaled by a factor between 0.9
                and 1.1 and the neural network prediction with the smallest MSE will be selected. If ``polish=True``,
                this step will happen before the LMS fit. If ``optimize_q=True``, this will step will happen after
                the q shift optimization.
            n_scale_samples: Number of curve scaling samples that will be generated. More samples can lead to a better
                result, but will increase the prediction time.
            identifier: identifier that is passed through to ensure data correlation

        Returns:
            :class:`FitResult`: An object that contains the fit results as well as useful methods to plot and save
                the results.
        """
        corrected_intensity = np.atleast_2d(corrected_intensity)

        # ~ test = dict(
        # ~ corrected_curve=corrected_intensity,
        # ~ q_values=q_values,
        # ~ dq=dq,
        # ~ factor=factor,
        # ~ polish=polish,
        # ~ fraction_bounds=fraction_bounds,
        # ~ optimize_q=optimize_q,
        # ~ n_q_samples=n_q_samples,
        # ~ optimize_scaling=optimize_scaling,
        # ~ n_scale_samples=n_scale_samples,
        # ~ )
        # ~ print("################### input data ##################")
        # ~ pprint(test)
        # ~ print("################### end input data ##################")

        fit_output = self._curve_fitter.fit_curve(
            corrected_curve=corrected_intensity,
            q_values=q_values,
            dq=dq,
            factor=factor,
            polish=polish,
            fraction_bounds=fraction_bounds,
            optimize_q=optimize_q,
            n_q_samples=n_q_samples,
            optimize_scaling=optimize_scaling,
            n_scale_samples=n_scale_samples,
        )

        predicted_refl = fit_output["predicted_reflectivity"]

        # ~ print("################### predicted_reflectivity##################")
        # ~ print(predicted_refl)
        # ~ print("################### end predicted_reflectivity ##################")

        predicted_parameters = fit_output["predicted_parameters"]
        if fit_output["best_q_shift"] is None:
            best_q_shift = None
        else:
            best_q_shift = fit_output["best_q_shift"][0]

        fit_result = FitResult(
            scan_number=0,
            timestamp=None,
            corrected_reflectivity=corrected_intensity,
            q_values_input=q_values,
            predicted_reflectivity=predicted_refl,
            q_values_prediction=self._trained_model.q_values - dq,
            predicted_parameters=predicted_parameters,
            best_q_shift=best_q_shift,
            sample=self._trained_model.sample,
        )
        # ~ if plot:
        # ~ parameters = [self.trained_model.sample.layers[-1].name + param for param in ('_thickness', '_roughness',
        # ~ '_sld')]
        # ~ fit_result.plot_prediction(parameters)
        # ~ fit_result.plot_sld_profile()
        # TODO transform into named tuple

        q_values_prediction = self._trained_model.q_values - dq
        return (
            identifier,
            predicted_parameters,
            predicted_refl,
            q_values_prediction,
            fit_result,
        )

    # ~ def set_footprint_params(self, wavelength: float, sample_length: float, beam_width: float,
    # ~ beam_shape: str = 'gauss', normalize_to: str = 'max'):
    # ~ """Set the parameters necessary to apply footprint correction.

    # ~ Args:
    # ~ wavelength: Photon wavelength in Angstroms.
    # ~ sample_length: Sample length along the beam direction in mm.
    # ~ beam_width: Beam width along the beam direction (height). For a gaussian beam profile this is the full
    # ~ width at half maximum.
    # ~ beam_shape:
    # ~ ``'gauss'`` (default) for a gaussian beam profile
    # ~ ``'box'`` for a box profile
    # ~ normalize_to:
    # ~ ``'max'`` (default): normalize data by the highest intensity value
    # ~ ``'first'``: normalize data by the first intensity value
    # ~ """

    # ~ params = {
    # ~ 'wavelength': wavelength,
    # ~ 'beam_width': beam_width,
    # ~ 'sample_length': sample_length,
    # ~ 'beam_shape': beam_shape,
    # ~ 'normalize_to': normalize_to
    # ~ }

    # ~ self._footprint_params.update(params)


class DefaultTangoFitter(TangoFitter):
    """:class:`SpecFitter` that is initialized with a pre-trained model for reflectivity on single-layer systems on
    Si/SiOx."""

    def __init__(self):
        super().__init__()
        self.set_trained_model(DefaultTrainedModel())
