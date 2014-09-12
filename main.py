#!/usr/bin/env python2

import os
from os import path
import time

import panel

from herbstclient import *
from daemon import *

key_modifier = "Mod4"

def wallpaper_loop():
    image_dir = os.path.join(os.path.dirname(__file__), "wallpapers", "images")
    while True:
        os.system("feh --randomize --recursive --bg-fill " + image_dir)
        time.sleep(500)

singleton("wallpaper", wallpaper_loop)

def battery_notify_loop():
    sent = False
    while True:
        perc = 0
        discharging = False
        for line in command_stream("upower", "-d"):
            if line.startswith("    percentage:"):
                perc = int(line[25:-2])
                if perc > 0:
                    break
            elif line.startswith("    state:") and line[25:-1] == "discharging":
                discharging = True
        if discharging and perc > 0 and perc < 15:
            if not sent:
                sent = True
                command("notify-send", "--urgency=critical", "--expire-time=20000", "Battery Low!", "Battery charge below 15%")
        else:
            sent = False
        time.sleep(30)

singleton("battery-warning", battery_notify_loop)    

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

for monitor in hc_stream("list_monitors"):
    print "Preparing monitor " + monitor
    panel.launch(monitor[:monitor.index(":")])
