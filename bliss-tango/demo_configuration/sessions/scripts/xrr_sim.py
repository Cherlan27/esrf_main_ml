from bliss.common.counter import SamplingMode, SoftCounter
from bliss.common.soft_axis import SoftAxis

import numpy as np
from scipy import interpolate


class XRR_Sim_Diode:
    """To be used in ascan as SoftAxis and SoftCounter at the same time"""

    def __init__(self):
        # abs pass definetly not good coding style, could/should be fixed later...
        exp_demo_data = np.loadtxt(
            "/home/esrf/Documents/closed_loop_beamtime/bliss-tango/demo_configuration/sessions/scripts/mlreflect_demo_scan.csv",
            skiprows=1,
            delimiter=",",
        )
        self._tth = exp_demo_data[:, 0] * 2.0
        self._transm = exp_demo_data[:, 4]
        self._f_transm = interpolate.interp1d(self._tth, self._transm)
        self._refl = np.log10(exp_demo_data[:, 5] / self._transm)
        self._f_refl = interpolate.interp1d(
            self._tth, np.log10(exp_demo_data[:, 5] / self._transm)
        )

        self.pos = np.min(self._tth)
        print(f"tth min:{np.min(self._tth)}, tth max:{np.max(self._tth)}")

    # ~ def _interp_reflectivity(self, q_interp, q, reflectivity):
    # ~ """Interpolate data on a base10 logarithmic scale."""
    # ~ return 10 ** np.interp(q_interp, q, np.log10(reflectivity))

    def read_transm(self):
        return self._f_transm(self.pos)

    def read_refl(self):
        return 10 ** self._f_refl(self.pos)

    def read_filtered_refl(self):
        return self.read_refl() * self.read_transm()

    @property
    def position(self):
        return self.pos

    @position.setter
    def position(self, val):
        self.pos = val
