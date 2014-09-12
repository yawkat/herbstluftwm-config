#!/usr/bin/env python2

import os
from os import path
import threading
import signal
import sys
import traceback

source_dir = path.dirname(__file__)

def run_fork(name, function):
    child_pid = os.fork()
    if child_pid is 0:
        log_dir = path.join(source_dir, "log")
        flags = os.O_CREAT | os.O_WRONLY | os.O_TRUNC
        os.dup2(os.open(path.join(log_dir, name + ".out"), flags), 1)
        os.dup2(os.open(path.join(log_dir, name + ".err"), flags), 2)
        log("Output redirected")
        try:
            function()
        except:
            log("Error!")
            traceback.print_exc()
        sys.exit(0)
    return child_pid

def run_thread(name, function, daemon=True):
    thread = threading.Thread(name=name, target=function)
    thread.daemon = daemon
    thread.start()

def singleton(name, function):
    pid_file = path.join(source_dir, "pid", name + ".pid")
    if path.isfile(pid_file):
        with open(pid_file, "r") as fd:
            try:
                os.kill(int(fd.read()), signal.SIGTERM)
            except:
                pass
    child_pid = run_fork(name, function)
    with open(pid_file, "w") as fd:
        fd.write(str(child_pid))

def log(msg, err=False):
    chan = 1
    if err:
        chan = 2
    os.write(chan, msg + "\n")
