# taken from mlreflect/data_generation/interpolation.py

import numpy as np


def interp_reflectivity(q_interp, q, reflectivity):
    """Interpolate data on a base10 logarithmic scale."""
    return 10 ** np.interp(q_interp, q, np.log10(reflectivity))
