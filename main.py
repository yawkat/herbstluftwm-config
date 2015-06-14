#!/usr/bin/env python2

import os
from os import path
import time

import panel
import upower
import wallpaper

from herbstclient import *
from daemon import *

key_modifier = "Mod4"

# loop that checks primary battery status every 30 secs and warns if it goes below 15%
def battery_notify_loop():
    notify_steps = (.05, .15)
    notify_sent = [False for x in notify_steps]
    while True:
        upower.instance.update_upower(min_age=30)
        if len(upower.instance.devices) is not 0:
            device = upower.instance.devices[0]
            if device.valid:
                if device.state is upower.STATE_NOT_CHARGING:
                    displayed = False
                    for i in range(len(notify_steps)):
                        if device.charge <= notify_steps[i]:
                            if not notify_sent[i]:
                                notify_sent[i] = True
                                if not displayed:
                                    displayed = True
                                    command(
                                        "notify-send", 
                                        "--urgency=critical", 
                                        "Battery Low!", 
                                        "Battery charge is %d%%" % (device.charge * 100)
                                    )
                        else:
                            notify_sent[i] = False
                else:
                    notify_sent = [False for x in notify_steps]
        time.sleep(30)
singleton("battery-warning", battery_notify_loop)

# network manager tray app
command_singleton("nm-applet", ("nm-applet",), delay=2)

# volume keys
command_singleton("volumed", ("xfce4-volumed", "--no-daemon"))

# hotkeys
command_singleton("hotkeys", ("xbindkeys",))

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
command_singleton("panel", ("java", "-Xmx100M", "-XX:+PrintGC", "-XX:+PrintGCDateStamps", "-XX:+UseSerialGC", "-jar", "wm.jar"))
def bind_overlay(key, path):
    bind(("Mod4", key), ("spawn", os.path.join(os.path.dirname(__file__), path), str(1366)))
#bind_overlay("plus", "run/toggle.sh")
bind_overlay("BackSpace", "password/ui.py")
screens = []
for monitor in hc_stream("list_monitors"):
#    print "Preparing monitor " + monitor
#    panel.launch(monitor[:monitor.index(":")])
    screens.append(map(int, hc("monitor_rect", monitor).strip().split(" ")))

wallpaper.start(screens)
