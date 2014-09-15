#!/usr/bin/env python2

import os
from os import path
import time

import panel
import upower

from herbstclient import *
from daemon import *

key_modifier = "Mod4"

# loop that replaces the wallpaper every 5 mins
def wallpaper_loop():
    image_dir = os.path.join(os.path.dirname(__file__), "wallpapers", "images")
    while True:
        os.system("feh --randomize --recursive --bg-fill " + image_dir)
        time.sleep(300)
singleton("wallpaper", wallpaper_loop)

# loop that checks primary battery status every 30 secs and warns if it goes below 15%
def battery_notify_loop():
    sent = False
    while True:
        upower.instance.update_upower(min_age=30)
        if len(upower.instance.devices) is not 0:
            device = upower.instance.devices[0]
            if device.valid:
                log("State: %s  Charge: %s" % (device.state, device.charge))
                if device.state is upower.STATE_NOT_CHARGING and device.charge < 0.15:
                    if not sent:
                        sent = True
                        command("notify-send", "--urgency=critical", "--expire-time=20000", "Battery Low!", "Battery charge below 15%")
                else:
                    sent = False
        time.sleep(30)
singleton("battery-warning", battery_notify_loop)

# network manager tray app
def nmapplet():
    command("nm-applet")
singleton("nm-applet", nmapplet, delay=2)

# volume keys
def volumed():
    command("xfce4-volumed", "--no-daemon")
singleton("volumed", volumed)

# tags
tags = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")
try:
    hc("rename", "default", tags[0])
except:
    pass
i = 0
for tag in tags:
    print "Preparing tag " + tag
    hc("add", tag)
    bind((key_modifier, tag), ("use_index", i))
    bind((key_modifier, "Shift", tag), ("move_index", i))
    i += 1

# make panels
for monitor in hc_stream("list_monitors"):
    print "Preparing monitor " + monitor
    panel.launch(monitor[:monitor.index(":")])
