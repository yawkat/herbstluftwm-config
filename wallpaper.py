#!/usr/bin/env python2

import os
import random
import sys
import daemon
from daemon import logger
import subprocess
import threading
import time
import datetime
import math
import colorsys

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageFilter

_fifo_file = os.path.join(os.path.dirname(__file__), ".wallpaper_fifo");

_diashow_time = 300

_padding = 2

_font = None

days_remaining_map = []

walked = 0
for i in range(3 * 4 * 7):
    days_remaining_map.append(walked)
    if i % 7 not in (5, 6) and i != 30 and i != 44 and i != 60:
        walked += 1
days_remaining_map = [walked - i for i in days_remaining_map]
days_remaining_map[0:0] = [0 for x in range(5)]

def _decorate_wallpaper(fr, to, size, image_format):
    f = os.path.basename(fr)

    img = Image.open(fr).convert(mode="RGBA")
    awidth, aheight = size
    width, height = img.size
    if awidth > width or aheight > height:
        logger.info("'%s' is too small" % f)
        open(to, "w").close() # touch with 0B
        return

    global _font
    if _font is None:
        logger.info("Loading font")
        _font = ImageFont.truetype("/usr/share/fonts/truetype/source-code-pro/SourceCodePro-Regular.ttf", 12)

    logger.info("Decorating '%s'" % f)

    # scale to size
    scale_factor = max(float(awidth) / width, float(aheight) / height)
    img.thumbnail((int(width * scale_factor), int(height * scale_factor)), Image.ANTIALIAS)

    width, height = img.size

    x = int((width - awidth) / 2)
    y = int((height - aheight) / 2)
    img = img.crop((x, y, x + awidth, y + aheight))

    width, height = img.size

    # read image name (file name - extension)
    ext_index = f.rfind(".")
    if ext_index is -1:
        image_name = f
    else:
        image_name = f[:ext_index]

    # prepare image drawing
    tw, th = ImageDraw.Draw(img).textsize(image_name, font=_font)
    th += 2
    tx, ty = _padding, height - th - _padding
    text_box = tx - _padding, ty - _padding, tx + tw + _padding, ty + th + _padding

    background_pixels = img.crop(text_box).getdata()
    # average image color for text theme
    background_average = tuple(map(lambda col: int(sum(col) / len(col)), zip(*background_pixels)))[:3]
    background_average_hsv = colorsys.rgb_to_hsv(*map(lambda x: x / 255., background_average))
    text_color_hsv = list(background_average_hsv)
    box_color_hsv = list(background_average_hsv)
    logger.info(str(text_color_hsv))
    # change values (brightness) of the colors so they become easier to see
    if text_color_hsv[2] > 0.5:
        text_color_hsv[2] -= 0.2
        box_color_hsv[2] += 1
    else:
        text_color_hsv[2] += 0.2
        box_color_hsv[2] = 0
    text_color = tuple(map(lambda x: int(x * 255), colorsys.hsv_to_rgb(*text_color_hsv)))
    box_color = tuple(map(lambda x: int(x * 255), colorsys.hsv_to_rgb(*box_color_hsv)))

    # draw and blur text for text shadow
    text_blurred = img.crop(text_box)
    # draw 5 times with diofferent offsets so we get a wider shadow
    for off in ((0, 0), (-1, 0), (1, 0), (0, 1), (0, -1)):
        ImageDraw.Draw(text_blurred).text((2 + off[0], off[1]), image_name, fill=box_color, font=_font)
    # blur shadow
    text_blurred = text_blurred.filter(ImageFilter.GaussianBlur(7))
    img.paste(text_blurred, box=text_box)
    
    # add normal text on top
    ImageDraw.Draw(img).text((tx, ty - 2), image_name, fill=text_color, font=_font)

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
        self.safe_mode = False

    def start(self):
        if not os.path.exists(_fifo_file):
            os.mkfifo(_fifo_file)

        if not os.path.exists(self.sized_image_dir):
            os.makedirs(self.sized_image_dir)

        loop = threading.Thread(target=self.loop_wallpaper)
        loop.daemon = True
        loop.start()

    def loop_wallpaper(self):
        while True:
            remaining = _diashow_time + self.last_update - time.time()
            if remaining < 2:
                self.change_wallpaper(+1)
                remaining = _diashow_time
            time.sleep(remaining)

    def change_wallpaper(self, step):
        if self.safe_mode:
            return
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
        self.show_wallpaper(path)
        logger.info("Changed wallpaper by %s to %s" % (step, path))

    def show_safe_wallpaper(self):
        today = datetime.date.today().timetuple().tm_yday
        today_days_remaining = days_remaining_map[today]
        with open("safe_wallpaper.svg") as f:
            svg = f.read()
        svg = svg.replace("####", str(today_days_remaining))
        cache_dir = os.path.join(".cache", "safe_wallpaper", str(today))
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            with open(os.path.join(cache_dir, "wp.svg"), "w") as f:
                f.write(svg)
            subprocess.Popen(("inkscape", "-z", "-e", os.path.join(cache_dir, "wp.png"), os.path.join(cache_dir, "wp.svg")), stdout=1, stderr=2).wait()
        self.show_wallpaper(os.path.join(cache_dir, "wp.png"))

    def show_wallpaper(self, path):
        dimensions_str = "%sx%s+%s+%s" % (self.dimensions[2], self.dimensions[3], self.dimensions[0], self.dimensions[1])
        logger.info("show " + dimensions_str)
        subprocess.Popen(("feh", "--bg-center", "--no-fehbg", "-g", dimensions_str, path), stdout=1, stderr=2)

def start(dimensions):
    logger.info("Start %s" % (dimensions,))
    def do_start():
        screens = []
        for dim in dimensions:
            x, y, w, h = dim
            dae = _Daemon(dim)
            dae.start()
            screens.append(dae)
        logger.info("Daemons: %s" % screens)
        while True:
            with open(_fifo_file, "r") as f:
                for delta in f:
                    delta = delta[:-1]
                    print("Got command %s" % delta)
                    if delta == "toggle_safe":
                        for screen in screens:
                            screen.safe_mode = not screen.safe_mode
                            if screen.safe_mode:
                                screen.show_safe_wallpaper()
                            else:
                                screen.change_wallpaper(1)
                        continue
                    try:
                        for screen in screens:
                            screen.change_wallpaper(int(delta))
                    except ValueError:
                        logger.error("Invalid delta %s" % delta)

    daemon.singleton("wallpaper", do_start)

if __name__ == '__main__':
    fd = os.open(_fifo_file, os.O_WRONLY | os.O_NONBLOCK)
    os.write(fd, sys.argv[1] + "\n")
    os.close(fd)
