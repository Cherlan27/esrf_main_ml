import gevent
from enum import IntEnum
from time import time as epoch
from scipy.interpolate import interp1d
from gevent import lock
from gevent.time import sleep
import gevent
import numpy as np
from bliss.common import greenlet_utils

TIMER_GREENLET=list()

class ActionTimer:
    def __init__(self, target_d, t0=0, d0=0, n_min=2, n_max=3, sleep=10):
        self.states = IntEnum(
            "ActionTimerStates",
            ["init", "started", "waiting", "triggered", "done", "stopped"],
        )
        self.status = self.states.init
        self.action = None
        self.action_args = None
        self.n_max = n_max
        self.n_min = n_min
        self.target_d = target_d
        self.interp_func = None
        self.sleep_time = sleep
        self.__lock = lock.Semaphore()
        self.__greenlet = None

        if t0 <= 0:
            t0 = epoch() - t0
        self.times = [t0]
        self.d = [d0]

    def set_action(self, func, *args):
        self.action = func
        self.action_args = args

    def add_next(self, d, t=0):
        
        if np.mean(np.array(self.d)) > d:
            return

        if t <= 0:
            t = epoch() - t
        self.times.append(t)
        self.d.append(d)

        if len(self.times) > self.n_max:
            self.times.pop(0)
            self.d.pop(0)

        print("times", self.times, "d", self.d)

        self.interp_func = interp1d(
            np.array(self.d), np.array(self.times), fill_value="extrapolate"
        )

        if self.status < self.states.started and len(self.times) >= self.n_min:
            self.start()
        else:
            self._update()

    def _run(self):
        global TIMER_GREENLET
        # ~ if self.status>=self.states.started:
        # ~ raise RuntimeError

        action_time = self.interp_func(self.target_d)
        current_time = epoch()

        print("current", current_time, "action", action_time)

        @greenlet_utils.protect_from_kill
        def run_action():
            self.status = self.states.triggered
            print("trigger action")
            self.action(*self.action_args)

        with self.__lock:
            if current_time < action_time:
                self.status = self.states.waiting
                print(f"waiting for {action_time-current_time}")
                sleep(action_time - current_time)

            g = gevent.spawn(run_action)
            TIMER_GREENLET.append(g)
            g.join()

        self.status = self.states.done

    def start(self):
        self.__greenlet = gevent.spawn(self._run)

    def _update(self):
        self.__greenlet.kill(block=True)
        with self.__lock:
            pass
        self.__greenlet = gevent.spawn(self._run)

    def stop(self):
        self.__greenlet.kill(block=True)
