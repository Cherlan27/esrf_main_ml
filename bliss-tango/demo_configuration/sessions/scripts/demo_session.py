from bliss.shell.standard import wm
from bliss.setup_globals import slit_vertical_gap, slit_vertical_offset


def ws():
    """where slit: helper function"""
    return wm(slit_vertical_gap, slit_vertical_offset)
