#!/usr/bin/env python2

import os

image_dir = os.path.join(os.path.dirname(__file__), "wallpapers", "images")

def update_wallpaper():
    os.system("feh --randomize --recursive --bg-fill " + image_dir)

if __name__ == '__main__':
    update_wallpaper()
