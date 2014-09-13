#!/usr/bin/env python2

# nstat (bandwidth monitor) access

import time
import daemon

up = 0
down = 0
# weight of the new value in the moving average
_weight = 0.2

def update():
    global up, down
    # lower moving avg
    up *= 1 - _weight
    down *= 1 - _weight
    for line in daemon.command_stream("nstat", "-t", "1"):
        if line[0] == "#":
            continue
        name = line[:32].strip()
        value = int(line[32:50].strip())
        if name == "IpExtInOctets":
            down += value * _weight
        elif name == "IpExtOutOctets":
            up += value * _weight

units = ("B", "K", "M", "G")

# converts the given number to a human-readable representation with 1024-suffixes
def human_readable(num):
    for unit in units[:-1]:
        if num < 1000:
            return "%05.1f%s" % (num, unit)
        num /= 1024.0
    return "%05.1f%s" % (num, units[-1])

# run nstat once and ignore its first value
update()
up = down = 0
