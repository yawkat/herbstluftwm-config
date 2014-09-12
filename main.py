#!/usr/bin/env python2

import os
from os import path
import time

import panel

from herbstclient import *
from daemon import *

key_modifier = "Mod4"

def wallpaper_loop():
    image_dir = os.path.join(os.path.dirname(__file__), "Wallpapers", "images")
    while True:
        os.system("feh --randomize --recursive --bg-fill " + image_dir)
        time.sleep(500)

singleton("wallpaper", wallpaper_loop)

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
