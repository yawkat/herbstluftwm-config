#!/usr/bin/env python2

import daemon

def run():
    import main

daemon.singleton("main", run)
