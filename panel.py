#!/usr/bin/env python2

import sys
import subprocess
import re
import time
import psutil

import upower
import gradient

from herbstclient import *
from daemon import *

background = "#002b36"
foreground = "#93a1a1"
height = 18
font = "-*-fixed-medium-*-*-*-12-*-*-*-*-*-*-*"

###

separator="^bg()^fg(" + background + ")|^fg(" + foreground + ")"
format_re = re.compile(r"\^[^(]*\([^)]*\)")

class Task():
    def __init__(self, task, interval):
        self.task = task
        self.interval = interval
        self._next = 0

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
            Task(self.update_battery, 20)
        ]

        self.window_title = ""
        self.battery = ""
        self.date = ""
        self.load = ""
        self.load_weighted = 0
        self.tag_string = ""

    def launch(self):
        hc("pad", self.monitor, height)

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

        run_thread("tasks_" + self.monitor, self.run_tasks)

        self.update()

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
            if update:
                self.update()
            time.sleep(1)

    def update_tags(self):
        val = ""
        tags = hc("tag_status").strip().split("\t")
        log("Tags: " + str(tags))
        for tag in tags:
            name = tag[1:]
            code = tag[0]
            val += "^bg()"
            if code == "#":
                val += "^fg(#fdf6e3)"
            elif code == "+" or code == "!":
                val += "^fg(#cb4b16)"
            elif code == ":":
                val += "^fg(#93a1a1)"
            else:
                val += "^fg(#586e75)"
            val += "^ca(1,herbstclient use \"" + name + "\") "
            val += name
            val += " ^ca()"
        self.tag_string = val

    def update_battery(self):
        upower.global_battery.update_upower()
        self.battery = " | ".join(upower.global_battery.components)

    def update_date(self):
        self.date = time.strftime("%Y-%m-%d, %H:%M:%S")

    def update_load(self):
        def perc(perc, name):
            col = gradient.fraction_color(1 - perc * 0.01)
            return "^fg(#%s)%s:%04.1f%%" % (col, name, perc)

        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        swap = psutil.swap_memory().percent
        self.load_weighted = self.load_weighted * 0.8 + cpu * 0.2

        self.load = perc(self.load_weighted, "C") + " " + perc(mem, "M") + " " + perc(swap, "S") + "^fg()"

    def update(self):
        val = ""
        val += self.tag_string
        val += separator + " "
        val += self.window_title.replace("^", "^^")

        right = separator + "^bg() "
        right += self.date
        right += " " + separator + " "
        right += self.load
        right += " " + separator + " "
        right += self.battery

        right_no_format = format_re.sub("", right)
        right_width = text_width(right_no_format + (" " * 8))

        val += "^pa(" + str(self.dimensions[2] - right_width) + ")"
        val += right

        val += "\n"
        log("New bar: " + val)
        self.dzen2.stdin.write(val)

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

def text_width(text):
    return int(command("dzen2-textwidth", font, text.encode('ascii','ignore')))

def launch(monitor):
    singleton("panel_" + monitor, lambda: do_launch(monitor))

def do_launch(monitor):
    log("do_launch " + monitor)
    Panel(monitor).launch()

