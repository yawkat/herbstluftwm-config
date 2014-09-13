#!/usr/bin/env python2

import time
import herbstclient

up = 0
down = 0
_weight = 0.2

def update():
    global up, down
    up *= 1 - _weight
    down *= 1 - _weight
    for line in herbstclient.command_stream("nstat", "-t", "1"):
        if line[0] == "#":
            continue
        name = line[:32].strip()
        value = int(line[32:50].strip())
        #print name, value
        if name == "IpExtInOctets":
            down += value * _weight
        elif name == "IpExtOutOctets":
            up += value * _weight

units = ("B", "K", "M", "G")

def human_readable(num):
    for unit in units[:-1]:
        if num < 1024:
            return "%4.1f%s" % (num, unit)
        num /= 1024.0
    return "%4.1f%s" % (num, units[-1])

update()
up = down = 0
