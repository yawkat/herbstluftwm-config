#!/usr/bin/env python2

import sys
import time
import herbstclient
import gradient
import time

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

STATE_NOT_CHARGING = 0
STATE_CHARGING = 1
STATE_UNKNOWN = -1

class Device():
    def __init__(self):
        self.charge = 0
        self.state = STATE_UNKNOWN
        self.finish_time = 0

    def format_panel(self):
        if self.state is STATE_NOT_CHARGING:
            state = u"-"
        elif self.state is STATE_CHARGING:
            state = u"+"
        else:
            state = u"?"
        if self.finish_time is 0:
            finish_time = ""
        else:
            finish_time = " " + str(self.finish_time) + "m"
        color = gradient.fraction_color(self.charge * 0.01)
        return "^fg(#%s)%s%%^fg()%s %s" % (color, self.charge * 100, finish_time, state.encode("utf-8"))

    @property
    def valid(self):
        return self.charge > 0

class Power():
    def __init__(self):
        self.devices = []
        self.last_update = 0

    def update(self, lines):
        devices = []
        reading = Device()

        self.components = []
        for line in lines:
            if line.startswith("Device: "):
                if reading.valid:
                    devices.append(reading)
                    reading = Device()
            elif line.startswith("    percentage:"):
                reading.charge = int(line[25:-2]) * 0.01
            elif line.startswith("  model:"):
                reading.model = line[24:-1]
            elif line.startswith("    state:"):
                if line[25:-1] == "charging":
                    reading.state = STATE_CHARGING
                elif line[25:-1] == "discharging":
                    reading.state = STATE_NOT_CHARGING
            elif line.startswith("    time to"):
                reading.finish_time = ptime(line[25:-1])
        if reading.valid:
            devices.append(reading)

        self.devices = devices

    def update_upower(self, min_age=0):
        if min_age > 0:
            stamp = time.time()
            if stamp - self.last_update < min_age:
                return
            self.last_update = stamp
        self.update(herbstclient.command_stream("upower", "-d"))

instance = Power()
