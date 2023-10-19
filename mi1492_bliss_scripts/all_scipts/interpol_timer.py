from scipy.interpolate import interp1d


class InterpolationTimer:
    """To be used in ascan as SoftAxis and SoftCounter at the same time"""

    def __init__(self,t0,d0,d_action,action,params):
        """t0: epoch at start
           d0: thickness at start
           d_action: thickness at which action should be triggerd
           action: fucntion to call 
           params: parameters of action
        """

    @property
    def time_until_action(self):
    
        
_trinamic = _Trinamic()

shuttertimer = InterpolationTimer()
