#!/usr/bin/env python2

import os
import sys
import subprocess
import re
import time
import psutil

import upower
import gradient
import nstat
import wallpaper

from herbstclient import *
from daemon import *

background = "#002b36"
foreground = "#93a1a1"
height = 18
font = "-*-terminus-medium-*-*-*-12-*-*-*-*-*-*-*"

###

separator="^bg()^fg(" + foreground + ")"
format_re = re.compile(r"\^[^(]*\([^)]*\)")

# repeating task (update battery status etc)
class Task():
    def __init__(self, task, interval):
        self.task = task
        self.interval = interval
        self._next = 0

    # run this task if it's due, returns True if it was executed.
    def tick(self):
        if self._next <= 0:
            self.task()
            self._next = self.interval - 1
            return True
        else:
            self._next -= 1
            return False

class Panel():
    def __init__(self, monitor):
        self.monitor = monitor
        self.dimensions = map(int, hc("monitor_rect", monitor).strip().split(" "))
        self.tasks = [
            Task(self.update_date, 1),
            Task(self.update_load, 1),
            Task(self.update_traffic, 1),
            Task(self.update_battery, 5)
        ]

        self.window_title = ""
        self.battery = ""
        self.traffic = ""
        self.date = ""
        self.load = ""
        self.load_weighted = 0
        self.tag_string = ""
        self.save_energy = False

    def launch(self):
        hc("pad", self.monitor, height)

        # launch dzen (we pipe commands into its stdin to update the panel)
        dzen_line = ("dzen2",)
        dzen_line += ("-x", str(self.dimensions[0]))
        dzen_line += ("-y", str(self.dimensions[1]))
        dzen_line += ("-w", str(self.dimensions[2]))
        dzen_line += ("-fn", font)
        dzen_line += ("-h", str(height))
        dzen_line += ("-e", "button3=;button4=exec:herbstclient use_index -1;button5=exec:herbstclient use_index +1")
        dzen_line += ("-ta", "l")
        dzen_line += ("-bg", background)
        dzen_line += ("-fg", foreground)
        self.dzen2 = subprocess.Popen(dzen_line, stdin=subprocess.PIPE)

        self.update_tags()

        # start running thhe tasks
        run_thread("tasks_" + self.monitor, self.run_tasks)

        self.update()

        bind(("Mod4", "plus"), ("spawn", os.path.join(os.path.dirname(__file__), "run", "toggle.sh"), str(self.dimensions[2])))

        tray_position = self.dimensions[2] - 550
        geom = "1x1+%s+1" % tray_position
        geom_max = "1x1+%s+1" % tray_position
        # system tray
        def tray():
            command("stalonetray", "-c", "stalonetrayrc", "--geometry", geom, "--max-geometry", geom_max)
        singleton("tray_" + self.monitor, tray, delay=1)

        wallpaper.start((self.dimensions[0], self.dimensions[1], self.dimensions[2], self.dimensions[3]))

        # listen for events from 'herbstclient --idle' (panel switch, window events, etc)
        event_proc = hc_stream("--idle")
        log("Waiting for events ")
        while True:
            event = event_proc.readline()
            self.hc_event(event[:-1])

    def run_tasks(self):
        while True:
            update = False
            for task in self.tasks:
                update |= task.tick()
            # if a task ran, we need to update the panel
            if update:
                self.update()
            if self.save_energy:
                time.sleep(3)
            else:
                time.sleep(1)

    # update the tag display (selected tag etc)
    def update_tags(self):
        val = ""
        tags = hc("tag_status").strip().split("\t")
        log("Tags: " + str(tags))
        for tag in tags:
            name = tag[1:]
            code = tag[0]
            val += "^bg()"
            if code == "#": # selected
                val += "^fg(#fdf6e3)"
            elif code == "+" or code == "!": # notification
                val += "^fg(#cb4b16)"
            elif code == ":": # has apps on it
                val += "^fg(#93a1a1)"
            else: # empty
                val += "^fg(#586e75)"
            val += "^ca(1,herbstclient use \"" + name + "\") "
            val += name
            val += " ^ca()"
        self.tag_string = val

    # update the battery display
    def update_battery(self):
        upower.instance.update_upower(min_age=20)
        self.battery = " | ".join(map(upower.Device.format_panel, upower.instance.devices))

    # update the network traffic display
    def update_traffic(self):
        nstat.update()
        self.traffic = "^fg(#cb4b16)%s ^fg(#b58900)%s" % (nstat.human_readable(nstat.down), nstat.human_readable(nstat.up))

    # update the timestamp
    def update_date(self):
        self.date = time.strftime("%Y-%m-%d, %H:%M:%S")

    # update the cpu/ram/swap display
    def update_load(self):
        def perc(perc, name):
            col = gradient.fraction_color(1 - perc * 0.01)
            return "^fg(#%s)%04.1f%%" % (col, perc)

        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        swap = psutil.swap_memory().percent
        self.load_weighted = self.load_weighted * 0.8 + cpu * 0.2

        self.load = perc(self.load_weighted, "C") + " " + perc(mem, "M") + " " + perc(swap, "S") + "^fg()"

    # rebuild the panel string and display it
    def update(self):
        # tags first
        val = ""
        val += self.tag_string
        val += separator + " "
        # current window title
        val += self.window_title.replace("^", "^^")

        save_energy_label = "^ca(1,herbstclient emit_hook save_energy_toggle)"
        if self.save_energy:
            save_energy_label += "^bg(#073642)^fg(#2aa198) S ^fg()^bg()"
        else:
            save_energy_label += " S "
        save_energy_label += "^ca()"

        # date and such on the right
        right = separator + "^bg() "
        right += (" " + separator + " ").join((self.date, self.load, self.traffic, save_energy_label, self.battery))

        # calculate right-aligned size
        right_no_format = format_re.sub("", right)
        right_width = text_width(right_no_format + " ")

        # padding for right-aligned text
        val += "^pa(" + str(self.dimensions[2] - right_width) + ")"
        val += right

        # newline to finish command for dzen2
        val += "\n"
        self.dzen2.stdin.write(val)

    # called when a herbstclient event occurs
    def hc_event(self, event):
        log("Event: " + event)
        if "\t" in event:
            t = event[:event.index("\t")]
        else:
            t = event
        if t.startswith("tag"):
            self.update_tags()
            self.update()
        elif t == "focus_changed" or t == "window_title_changed":
            self.window_title = "\t".join(event.split("\t")[2:])
            self.update()
        elif t == "quit_panel" or t == "reload":
            sys.exit()
        elif t == "save_energy_toggle":
            self.save_energy = not self.save_energy
            self.update()

def text_width(text):
    return int(command("dzen2-textwidth", font, text.encode('ascii','ignore')))

def launch(monitor):
    singleton("panel_" + monitor, lambda: _do_launch(monitor))

def _do_launch(monitor):
    Panel(monitor).launch()

