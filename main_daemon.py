#!/usr/bin/env python2

# run main.py as a daemonized singleton (killing any previous instance)

import daemon
daemon.init_logger()

def run():
    import main

daemon.singleton("main", run)
