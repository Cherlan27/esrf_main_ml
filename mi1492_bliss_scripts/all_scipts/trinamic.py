from bliss.common.soft_axis import SoftAxis

from bliss.common import tango


class _Trinamic:
    """To be used in ascan as SoftAxis and SoftCounter at the same time"""

    def __init__(self):
        proxy_uri="//id10tmp0.esrf.fr:10000/id00/trinamic/trinamic"
        self.proxy = tango.DeviceProxy(proxy_uri)


    @property
    def position(self):
        return self.proxy.do_wa()

    @position.setter
    def position(self, val):
        self.proxy.do_mv(val)
        
trinamic_obj = _Trinamic()

trinamic = SoftAxis("sample1", trinamic_obj)
