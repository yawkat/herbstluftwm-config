#!/usr/bin/env python2

# herbstclient access methods

from daemon import *
import subprocess

# run a herbstclient command and return its stdout
def hc_stream(*args):
    return command_stream(*(("herbstclient",) + tuple(args)))

# run a herbstclient command and return its output as a string
def hc(*args):
    return hc_stream(*args).read()

# create a keybind
# combination is an iterable of the keys that need to be pressed, command the action herbstclient should take.
def bind(combination, command):
    hc("keybind", *(("-".join(combination),) + command))
