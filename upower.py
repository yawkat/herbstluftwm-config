#!/usr/bin/env python2

import sys
import time
import herbstclient
import gradient

def ptime(time_string):
    number = float(time_string[:time_string.index(" ")].replace(",", "."))
    unit = time_string[time_string.index(" ")+1:]
    if unit == "days":
        number *= 24 * 60
    elif unit == "hours":
        number *= 60
    elif unit == "seconds":
        number /= 60
    return int(number)

class Power():
    def __init__(self):
        self.components = []
        self.reset_member()

    def reset_member(self):
        self.percentage = 0
        self.charging = -1
        self.finish_time = 0

    def pr(self):
        if self.charging is 0:
            state = u"-"
        elif self.charging is 1:
            state = u"+"
        else:
            state = u"?"
        if self.finish_time is 0:
            finish_time = ""
        else:
            finish_time = " " + str(self.finish_time) + "m"
        color = gradient.fraction_color(self.percentage * 0.01)
        self.components.append("^fg() %s ^fg(#%s)%s%%^fg()%s %s" % (self.model[:3], color, self.percentage, finish_time, state.encode("utf-8")))
        self.reset_member()

    def update(self, lines):
        self.components = []
        for line in lines:
            if line.startswith("Device: "):
                if self.percentage is not 0:
                    self.pr()
            elif line.startswith("    percentage:"):
                self.percentage = int(line[25:-2])
            elif line.startswith("  model:"):
                self.model = line[24:-1]
            elif line.startswith("    state:"):
                if line[25:-1] == "charging":
                    self.charging = 1
                elif line[25:-1] == "discharging":
                    self.charging = 0
            elif line.startswith("    time to"):
                self.finish_time = ptime(line[25:-1])
        if self.percentage is not 0:
            self.pr()
        else:
            self.reset_member()

    def update_upower(self):
        self.update(herbstclient.command_stream("upower", "-d"))

global_battery = Power()
