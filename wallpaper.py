#!/usr/bin/env python2

import os
import random
import sys
import daemon
import subprocess
import threading
import time
import math
import colorsys

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

_fifo_file = os.path.join(os.path.dirname(__file__), ".wallpaper_fifo");

_diashow_time = 300

_padding = 2

_font = None

def _decorate_wallpaper(fr, to, size, image_format):
    f = os.path.basename(fr)

    img = Image.open(fr)
    awidth, aheight = size
    width, height = img.size
    if awidth > width or aheight > height:
        daemon.log("'%s' is too small" % f)
        open(to, "w").close() # touch with 0B
        return

    global _font
    if _font is None:
        daemon.log("Loading font")
        _font = ImageFont.truetype("/usr/share/fonts/truetype/source-code-pro/SourceCodePro-Regular.ttf", 12)

    daemon.log("Decorating '%s'" % f)

    scale_factor = max(float(awidth) / width, float(aheight) / height)
    img.thumbnail((int(width * scale_factor), int(height * scale_factor)), Image.ANTIALIAS)

    width, height = img.size

    x = int((width - awidth) / 2)
    y = int((height - aheight) / 2)
    img = img.crop((x, y, x + awidth, y + aheight))

    width, height = img.size

    gfx = ImageDraw.Draw(img)
    ext_index = f.rfind(".")
    if ext_index is -1:
        image_name = f
    else:
        image_name = f[:ext_index]

    tw, th = gfx.textsize(image_name, font=_font)
    th += 2
    tx, ty = _padding, height - th - _padding
    text_box = tx - _padding, ty - _padding, tx + tw + _padding, ty + th + _padding
    text_bg_pixels = img.crop(text_box).getdata()
    text_bg_average = tuple(map(lambda col: int(sum(col) / len(col)), zip(*text_bg_pixels)))[:3]
    text_bg_average_hsv = colorsys.rgb_to_hsv(*map(lambda x: x / 255., text_bg_average))
    text_color_hsv = list(text_bg_average_hsv)
    if text_color_hsv[2] > 0.5:
        text_color_hsv[2] -= 0.1
    else:
        text_color_hsv[2] += 0.1
    text_color = tuple(map(lambda x: int(x * 255), colorsys.hsv_to_rgb(*text_color_hsv)))
    gfx.rectangle(text_box, fill=text_bg_average)
    gfx.text((tx, ty - 2), image_name, fill=text_color, font=_font)
    img.save(to, image_format)

class _Daemon():
    def __init__(self, dimensions):
        self.last_update = 0
        self.current_index = -1
        self.dimensions = dimensions
        self.size = dimensions[2], dimensions[3]
        self.sized_image_dir = os.path.join(os.path.dirname(__file__), ".cache", "wallpapers", "%sx%s" % self.size)
        image_dir = os.path.join(os.path.dirname(__file__), "wallpapers", "images")
        files = os.listdir(image_dir)
        self.wallpapers = [(os.path.join(self.sized_image_dir, name), os.path.join(image_dir, name)) for name in files]
        random.shuffle(self.wallpapers)

    def start(self):
        if not os.path.exists(_fifo_file):
            os.mkfifo(_fifo_file)

        if not os.path.exists(self.sized_image_dir):
            os.makedirs(self.sized_image_dir)

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
        i = 0
        while i != step:
            i += math.copysign(1, step)
            self.current_index = int((self.current_index + i) % len(self.wallpapers))
            path, original = self.wallpapers[self.current_index]
            if not os.path.exists(path):
                _decorate_wallpaper(original, path, self.size, "png")
            if os.stat(path).st_size == 0:
                self.wallpapers.pop(self.current_index)
                i -= math.copysign(1, step)
        dimensions_str = "%sx%s+%s+%s" % (self.dimensions[2], self.dimensions[3], self.dimensions[0], self.dimensions[1])
        subprocess.Popen(("feh", "--bg-center", "-g", dimensions_str, path), stdout=1, stderr=2)
        daemon.log("Changed wallpaper by %s to %s" % (step, path))

def start(dimensions):
    x, y, w, h = dimensions
    daemon.singleton("wallpaper_%sx%s+%s+%s" % (w, h, x, y), lambda: _Daemon(dimensions).start())

if __name__ == '__main__':
    fd = os.open(_fifo_file, os.O_WRONLY | os.O_NONBLOCK)
    os.write(fd, sys.argv[1] + "\n")
    os.close(fd)
