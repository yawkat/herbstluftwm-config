#!/usr/bin/env python2

import os
import random
import sys
import daemon
import subprocess
import threading
import time

_fifo_file = os.path.join(os.path.dirname(__file__), ".wallpaper_fifo");

_diashow_time = 300

class _Daemon():
    def __init__(self):
        self.last_update = 0
        self.current_index = -1
        image_dir = os.path.join(os.path.dirname(__file__), "wallpapers", "images")
        files = os.listdir(image_dir)
        self.wallpapers = [(os.path.join(image_dir, name), name) for name in files]
        random.shuffle(self.wallpapers)

    def start(self):
        if os.path.exists(_fifo_file):
            os.remove(_fifo_file)
        os.mkfifo(_fifo_file)

        loop = threading.Thread(target=self.loop_wallpaper)
        loop.daemon = True
        loop.start()

        self.manual_update_wallpaper()

    def loop_wallpaper(self):
        while True:
            remaining = _diashow_time + self.last_update - time.time()
            if remaining < 2:
                self.change_wallpaper(+1)
                remaining = _diashow_time
            time.sleep(remaining)

    def manual_update_wallpaper(self):
        while True:
            with open(_fifo_file, "r") as f:
                for delta in f:
                    try:
                        self.change_wallpaper(int(delta))
                    except ValueError:
                        daemon.log("Invalid delta %s" % delta)

    def change_wallpaper(self, step):
        self.last_update = time.time()
        self.current_index = (self.current_index + step) % len(self.wallpapers)
        path, name = self.wallpapers[self.current_index]
        subprocess.Popen(("feh", "--bg-fill", path), stdout=1, stderr=2)
        daemon.log("Changed wallpaper by %s to %s (%s)" % (step, path, name))

def _daemon():
    _Daemon().start()

def start():
    daemon.singleton("wallpaper", _daemon)

if __name__ == '__main__':
    with open(_fifo_file, "w") as f:
        f.write(sys.argv[1] + "\n")
