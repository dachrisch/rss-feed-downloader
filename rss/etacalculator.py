import sys
import time
import threading


class EtaCalculator(object):
    '''
    __author__ = 'Denis Barmenkov <denis.barmenkov@gmail.com>'
    __source__ = 'http://code.activestate.com/recipes/577002-precise-console-progress-meter-with-eta-calculatio/?in=user-57155'
    calculate ETA (Estimated Time of Arrival :)
    for some events

    Save few last update points or some seconds.
    Help fight statistics after hibernate :)
    '''
    
    def __init__(self, wanted_size, max_point=20, max_seconds=30):
        self.wanted_size = wanted_size
        self.points = list()
        self.max_point = max_point
        self.max_seconds = max_seconds
        self.points.append([time.time(), 0])
        self.eta = -1

    def _cleanup(self):
        if len(self.points) < 2:
            return 0
        else:
            last_point_time = self.points[-1][0]
            while len(self.points) > 2:
                if last_point_time - self.points[0][0] > self.max_seconds and \
                   len(self.points) > self.max_point:
                    self.points.pop(0)
                else:
                    break
            return 1

    def update(self, cursize):
        self.points.append([time.time(), cursize])
        if not self._cleanup():
            return

        delta_time = self.points[-1][0] - self.points[0][0]
        delta_work = cursize
        if delta_work == 0.0 or delta_time == 0.0:
            return 

        speed = float(delta_work) / float(delta_time)
        self.eta = (float(self.wanted_size) - float(cursize)) / float(speed)


