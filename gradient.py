#!/usr/bin/env python2

import colorsys

f = 1. / 0xff

fr = colorsys.rgb_to_hsv(0xdc * f, 0x32 * f, 0x2f * f)
to = colorsys.rgb_to_hsv(0x85 * f, 0x99 * f, 0x00 * f)

off = to[0] - fr[0], to[1] - fr[1], to[2] - fr[2]

def fraction_color(fraction):
    scaled = off[0] * fraction, off[1] * fraction, off[2] * fraction
    val = fr[0] + scaled[0], fr[1] + scaled[1], fr[2] + scaled[2]
    rgb = colorsys.hsv_to_rgb(val[0], val[1], val[2])
    rgb = rgb[0] * 0xff, rgb[1] * 0xff, rgb[2] * 0xff
    return "%02x%02x%02x" % rgb
