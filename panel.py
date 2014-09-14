#!/usr/bin/env python2

import sys
import subprocess
import re
import time
import psutil

import upower
import gradient
import nstat

from herbstclient import *
from daemon import *

from Tkinter import *

background = "#002b36"
foreground = "#93a1a1"
height = 18
font = "-*-fixed-medium-*-*-*-12-*-*-*-*-*-*-*"

###

separator="|"
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
        self.tasks = (
            Task(self.update_date, 1),
            Task(self.update_load, 1),
            Task(self.update_traffic, 1),
            Task(self.update_battery, 5)
        )

        self.window_title = ""
        self.battery = ""
        self.traffic = ""
        self.date = ""
        self.load = ""
        self.load_weighted = 0
        self.tag_string = ""

    def launch(self):
        hc("pad", self.monitor, height)

        '''
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
        '''

        self.frame = Frame()
        self.frame.master["bg"] = "black"
        self.frame.master.configure(background=background)
        self.frame.master.attributes("-type", "dock")
        self.frame.master.geometry("%sx%s+%s+%s" % (self.dimensions[2], height, self.dimensions[0], self.dimensions[1]))
        self.frame.pack(fill=BOTH, expand=True)

        self.right = Frame(self.frame)
        self.right.pack(side=RIGHT, fill=BOTH)
        self.left = Frame(self.frame)
        self.left.pack(side=LEFT, fill=BOTH, expand=True)

        self.tag_labels = []
        self.window_title_var = StringVar()
        self.battery_var = StringVar()
        self.traffic_var = StringVar()
        self.date_var = StringVar()
        self.load_var = StringVar()
        self.window_title_var.set("window_title")
        self.battery_var.set("battery")
        self.traffic_var.set("traffic")
        self.date_var.set("date")
        self.load_var.set("load")
        
        self.tag_frame = Frame(self.left)
        self.tag_frame.pack(side=LEFT, fill=BOTH)

        Label(self.left, bg=background, fg=foreground, textvariable=self.window_title_var).pack(side=LEFT, fill=BOTH)
        Label(self.right, bg=background, fg=foreground, textvariable=self.date_var).pack(side=LEFT, fill=BOTH)
        Label(self.right, bg=background, fg=foreground, textvariable=self.load_var).pack(side=LEFT, fill=BOTH)
        Label(self.right, bg=background, fg=foreground, textvariable=self.traffic_var).pack(side=LEFT, fill=BOTH)
        Label(self.right, bg=background, fg=foreground, textvariable=self.battery_var).pack(side=LEFT, fill=BOTH)

        self.update_tags()

        # start running thhe tasks
        run_thread("tasks_" + self.monitor, self.run_tasks)

        self.update()
        run_thread("herbstluftwm-event-listener", self.listen_events)
        self.frame.mainloop()

    def listen_events(self):
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
            time.sleep(1)

    # update the tag display (selected tag etc)
    def update_tags(self):
        val = ""
        tags = hc("tag_status").strip().split("\t")
        log("Tags: " + str(tags))
        i = 0
        for tag in tags:
            while i >= len(self.tag_labels):
                var = StringVar()
                label = Label(self.tag_frame, bg=background, textvariable=var, anchor="nw", justify="left")
                label.grid(row=0, column=i)
                self.tag_labels.append((label, var))
            label = self.tag_labels[i]
            name = tag[1:]
            code = tag[0]
            if code == "#": # selected
                color = "#fdf6e3"
            elif code == "+" or code == "!": # notification
                color = "#cb4b16"
            elif code == ":": # has apps on it
                color = "#93a1a1"
            else: # empty
                color = "#586e75"
            label[1].set(name)
            label[0].configure(foreground=color)
            i += 1
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

    def update(self):
        self.frame.after(0, self._update)

    # rebuild the panel string and display it
    def _update(self):
        ## tags first
        #val = ""
        #val += self.tag_string
        #val += separator + " "
        ## current window title
        #val += self.window_title.replace("^", "^^")

        ## date and such on the right
        #right = separator + "^bg() "
        #right += (" " + separator + " ").join((self.date, self.load, self.traffic, self.battery))

        ## calculate right-aligned size
        #right_no_format = format_re.sub("", right)
        #right_width = text_width(right_no_format + (" " * 8))

        ## padding for right-aligned text
        #val += "^pa(" + str(self.dimensions[2] - right_width) + ")"
        #val += right

        ## newline to finish command for dzen2
        #val += "\n"
        #self.dzen2.stdin.write(val)
        self.window_title_var.set(self.window_title)
        self.battery_var.set(self.battery)
        self.traffic_var.set(self.traffic)
        self.load_var.set(self.load)
        self.date_var.set(self.date)

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

def text_width(text):
    return int(command("dzen2-textwidth", font, text.encode('ascii','ignore')))

def launch(monitor):
    singleton("panel_" + monitor, lambda: _do_launch(monitor))

def _do_launch(monitor):
    Panel(monitor).launch()

