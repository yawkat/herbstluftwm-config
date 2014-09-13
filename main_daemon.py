#!/usr/bin/env python2

# run main.py as a deamonized singleton (killing any previous instance)

import daemon

def run():
    import main

daemon.singleton("main", run)
