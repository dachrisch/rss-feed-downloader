#!/usr/bin/python

"""Track and display progress, providing estimated completion time.

This module provides 2 classes to simply add progress display to any
application. Programs with more complex GUIs might still want to use it for the
estimates of time remaining it provides.

Use the ProgressDisplay class if your work is done in a simple loop:
from progress import *
for i in ProgressDisplay(range(500)):
    do_work()

If do_work() doesn't send any output to stdout you can use the following,
which will cause a single status line to be printed and updated:
from progress import *
for i in ProgressDisplay(range(500), display=SINGLE_LINE):
    do_work()

For more complex applications, you will probably need to manage a Progress
object yourself:
from progress import *
progress = Progress(task_size)
for part in task:
    do_work()
    progress.increment()
    progress.print_status_line()

If you have a more sophisticated GUI going on, you can still use Progress
objects to give you a good estimate of time remaining:
from progress import *
progress = Progress(task_size)
for part in task:
    do_work()
    progress.increment()
    update_gui(progress.percentage(), progress.time_remaining())

This code is released under the Python 2.6.2 license.
"""

__author__ = ("Tim Newsome <nuisance@casualhacker.net>")
__version__ = "1.0.0"

import time
import math

def _time():
    """Return time in seconds. I made a separate function so I can easily
    simulate an OS where that number is only accurate to the nearest second.
    """
    return time.time()

class Progress:
    """Contains all state for a progress tracker."""
    def __init__(self, total_work, unit=None, computer_prefix=None):
        """Create a new progress tracker.
        'total_work' is the units of work that will be done.
        'unit' is the unit to be displayed to the user.
        'computer_prefix' should be set to True if this unit requires prefix
        increments of 1024 instead of the traditional 1000. If it is not set,
        then the class tries to guess based on 'unit'.
        """
        self.total_work = total_work
        self.unit = unit
        if computer_prefix is None and not self.unit is None:
            self.computer_prefix = unit.lower() in ["b", "bit", "byte"]
        else:
            self.computer_prefix = computer_prefix
        self.history = []
        self.log = []
        self.predicters = [self.predicted_rate, self._predicted_rate_period,
            self._predicted_rate_avg, self._predicted_rate_pessimist]
        self.update(0)
        # Store away the beginning time so we can report the overall work rate.
        self.start = self.history[0]
    

        # stats for predicted_rate_pessimist
        self.pes_squares = 0
        self.pes_total = 0
        self.pes_samples = 0
    
    def update_incremental(self, delta_work):
        self.update(self.history[-1][0] + delta_work)

    def update(self, work):
        """Updates the work completed to 'work'."""
        if work > self.total_work:
            self.total_work = work
        t = _time()
    
        history_entry = (work, t)
    
        # Only add history elements if the time is different from the previous
        # time, and at least a second has elapsed.
        replace = (len(self.history) > 0 and t == self.history[-1][1]) or \
            (len(self.history) > 1 and
             self.history[-1][1] - self.history[-2][1] < 1)
    
        # Keep track of sum of squared(time) per unit of work.
        # This has to happen "atomically" with adding the elements to history.
        if not replace and len(self.history) > 1:
            # Base computation on the last 2 history entries instead of
            # (work, t) because the new entry will likely be replaced later.
            delta_t = float(self.history[-1][1] - self.history[-2][1])
            delta_w = self.history[-1][0] - self.history[-2][0]
            rate = delta_t / delta_w
            self.pes_squares += rate * rate
            self.pes_total += rate
            self.pes_samples += 1
    
        if replace:
            self.history[-1] = history_entry
        else:
            self.history.append(history_entry)

        log_entry = (work, t, map(apply, self.predicters))
        if replace:
            self.log[-1] = log_entry
        else:
            self.log.append(log_entry)

    def increment(self):
        """Increments the work completed by 1 unit."""
        self.update(self.history[-1][0] + 1)

    def percentage(self):
        """Returns the percent of work completed so far."""
        return 100.0 * self.history[-1][0] / self.total_work

    def done(self):
        """Returns True when all work is done."""
        return self.history[-1][0] == self.total_work

    def _predicted_rate_period(self):
        """Returns the predicted rate of work in units per second for the
        remainder of the work. Assumes that next n minutes will be like the
        last n minutes. In other words, if only 10% of work is remaining,
        only look to see how long it took to complete the last 10% of the
        work.
        """
        if len(self.history) < 2:
            return None
        work_done = self.history[-1][0]
        remaining_work = self.total_work - work_done
        # Drop all old history entries.
        while work_done - self.history[1][0] > remaining_work:
            self.history.pop(0)
        return float(self.history[-1][0] - self.history[0][0]) / \
            (self.history[-1][1] - self.history[0][1])

    def _predicted_rate_avg(self):
        """Returns the predicted rate of work in units per second for the
        remainder of the work. Assumes that next n minutes will be like the
        average has been so far.
        """
        if len(self.history) < 2:
            return None
        return float(self.history[-1][0] - self.start[0]) / \
            (self.history[-1][1] - self.start[1])

    def _predicted_rate_pessimist(self):
        """Returns the predicted rate of work in units per second for the
        remainder of the work. Assumes each remaining unit will take the time
        it takes to process 1 unit plus 1 standard deviation. Scale this
            pessimism by the percentage of work complete. This function is very
        unlikely to overestimate the work rate when the work is almost done.
        """
        if len(self.history) < 3:
            return self._predicted_rate_avg()
        avg = self.pes_total / self.pes_samples
        stddev = math.sqrt(self.pes_squares / self.pes_samples - avg * avg)
        return 1.0 / (avg + stddev * self.percentage() / 100)

    def predicted_rate(self):
        """Returns the predicted rate of work in units per second for the
        remainder of the work.
        """
        rate_1 = self._predicted_rate_period()
        if rate_1 is None:
            return None
        rate_3 = self._predicted_rate_pessimist()
        if rate_3 is None:
            return rate_1
        return (rate_1 + rate_3) / 2

    def overall_rate(self):
        """Returns the overall rate of work so far in units per second."""
        if self.time_elapsed() == 0:
            return 1
        return float(self.history[-1][0] - self.start[0]) / self.time_elapsed()

    def time_elapsed(self):
        return self.history[-1][1] - self.start[1]

    def time_remaining(self):
        """Returns the estimated amount of time (in seconds) remaining until
        all the work is complete."""
        work_rate = self.predicted_rate()
        if work_rate is None:
            return -1
        remaining_work = self.total_work - self.history[-1][0]
        work_time_remaining = remaining_work / work_rate
        work_time_elapsed = _time() - self.history[-1][1]
        return work_time_remaining - work_time_elapsed

    def eta(self):
        """Returns the time (similar to time.time()) when the work will be
        complete."""
        return _time() + self.time_remaining()

    def status_line(self, task=None):
        """Return a status line. Optionally a task name can be passed in to be
        included as well."""
        status = str(self)
        if task is None:
            line = status
        else:
            status += " | "
            line = "%s%s" % (status, task)
        return line

    def _grade_performance(self):
        """Go through the internal log to see how well time remaining was
        predicted. Returns average and standard deviation for the predicted
        time elapsed divided by the actual time elapsed."""
        end = self.log[-1]
        entry_count = 0
        algorithms = len(end[2])
        total = [0] * algorithms
        squares = [0] * algorithms
        average = [0] * algorithms
        stddev = [0] * algorithms
        # Ignore the first entry, since no prediction can be made based on
        # just one entry.
        for entry in self.log[1:-1]:
            for i in range(algorithms):
                predicted = entry[1] + (end[0] - entry[0]) / entry[2][i] - \
                        self.start[1]
                actual = end[1] - self.start[1]
                factor_percent = 100.0 * predicted / actual
                total[i] += factor_percent
                squares[i] += factor_percent * factor_percent
                entry_count += 1
        if entry_count == 0:
            return []
        for i in range(algorithms):
            average[i] = total[i] / entry_count
            stddev[i] = math.sqrt(squares[i] / entry_count - \
                average[i]*average[i])
        return zip(average, stddev)
