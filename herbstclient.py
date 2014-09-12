#!/usr/bin/env python2

from daemon import *
import subprocess

def command_stream(*components):
    components = map(lambda c: str(c), components)
    log("Executing " + str(components))
    return subprocess.Popen(components, stdout=subprocess.PIPE).stdout

def command(*components):
    return command_stream(*components).read()

def hc_stream(*args):
    return command_stream(*(("herbstclient",) + tuple(args)))

def hc(*args):
    return hc_stream(*args).read()

def bind(combination, command):
    hc("keybind", *(("-".join(combination),) + command))

def bind_directional(combination, function):
    for direction in ("left", "up", "right", "down"):
        bind(combination + (direction,), function(direction))
