#!/usr/bin/env python2

# upower (battery monitor) access

import sys
import time
import daemon
import gradient
import time

# parse a time string as used by upower -d
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

# device state
STATE_NOT_CHARGING = 0
STATE_CHARGING = 1
STATE_UNKNOWN = -1

class Device():
    def __init__(self):
        self.charge = 0
        self.state = STATE_UNKNOWN
        self.finish_time = 0

    # format for panel display
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
        color = gradient.fraction_color(1 - self.charge * 0.01)
        return "^fg(#%s)%s%%^fg()%s %s" % (color, self.charge * 100, finish_time, state.encode("utf-8"))

    @property
    def valid(self):
        # if charge is 0 the device either defaults to 0 or doesn't report charge at all and thus isn't a battery device (usually)
        return self.charge > 0

class Power():
    def __init__(self):
        self.devices = []
        self.last_update = 0

    def update(self, lines):
        devices = []
        reading = Device()

        self.components = []
        # parse upower output
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

    # parse from upower -d output if the data is older than min_age seconds
    def update_upower(self, min_age=0):
        if min_age > 0:
            stamp = time.time()
            if stamp - self.last_update < min_age:
                return
            self.last_update = stamp
        self.update(daemon.command_stream("upower", "-d"))

# instance that should only be used with Power.update_upower
instance = Power()
