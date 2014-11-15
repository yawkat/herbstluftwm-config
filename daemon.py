#!/usr/bin/env python2

# multithreading utils

from __future__ import print_function

import os
from os import path
import threading
import signal
import sys
import traceback
import time
import subprocess
import setproctitle
import multiprocessing
import logging

source_dir = path.dirname(__file__)

# list of pids of child processes started by command[_stream] and run_fork
_children = []

def _kill_children(sign):
    for child in _children:
        try:
            logger.debug("Sending %s to %s" % (sign, child))
            os.kill(child, sign)
        except:
            logger.exception("Failed to send signal", exc_info=True)

# run on exit, kill all children
def term(*args):
    # try term
    _kill_children(signal.SIGTERM)
    time.sleep(1)
    # force kill
    _kill_children(signal.SIGKILL)
signal.signal(signal.SIGTERM, term)

# run a command and return a stream of its stdout (pipe)
def command_stream(*components):
    components = map(lambda c: str(c), components)
    logger.debug("Executing " + str(components))
    proc = subprocess.Popen(components, stdout=subprocess.PIPE)
    _children.append(proc.pid)
    return proc.stdout

# run a command and return its stdout as a string
def command(*components):
    return command_stream(*components).read()

# fork-run the given function after <delay> seconds
# name is used for log files
def run_fork(name, function, delay=0):
    logger.info("Launching %s" % name)
    def run():
        global logger
        logger = _create_logger(name)
        try:
            time.sleep(delay)
            setproctitle.setproctitle(setproctitle.getproctitle() + " > " + name)
            function()
        except:
            logger.exception("Error in process execution", exc_info=True)
    proc = multiprocessing.Process(target=run)
    proc.start()
    return proc.pid

# run a daemon thread with the given name and target function
def run_thread(name, function, daemon=True):
    thread = threading.Thread(name=name, target=function)
    thread.daemon = daemon
    thread.start()

# run a singleton function (run_fork), killing any previous instances
def singleton(name, function, delay=0):
    pid_file = path.join(source_dir, "pid", name + ".pid")
    if path.isfile(pid_file):
        with open(pid_file, "r") as fd:
            try:
                pid = int(fd.read())
                os.kill(pid, signal.SIGTERM)
                def kill_final():
                    time.sleep(1)
                    os.kill(pid, signal.SIGKILL)
                # try kill too after 1s
                run_thread("kill_" + name, kill_final)
            except:
                pass
    child_pid = run_fork(name, function, delay=delay)
    with open(pid_file, "w") as fd:
        fd.write(str(child_pid))

def command_singleton(name, command_components, delay=0):
    singleton(name, lambda: command(*command_components), delay=delay)

def _create_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(levelname)8s] %(message)s")
    log_file = "log/" + name
    _rotate_logs(log_file)
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("Logger '%s' created", name)
    return logger

def _rotate_logs(base_file, index=0):
    if index == 0:
        name = base_file
    else:
        name = base_file + "." + str(index)
    if os.path.exists(name):
        if index >= 2:
            os.remove(name)
        else:
            next_name = _rotate_logs(base_file, index + 1)
            os.rename(name, next_name)
    return name

logger = None
def init_logger():
    global logger
    if logger is None:
        logger = _create_logger("main")

