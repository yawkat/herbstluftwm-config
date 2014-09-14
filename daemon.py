#!/usr/bin/env python2

# multithreading utils

import os
from os import path
import threading
import signal
import sys
import traceback
import time
import subprocess
import setproctitle

source_dir = path.dirname(__file__)

# list of pids of child processes started by command[_stream] and run_fork
_children = []

def _kill_children(sign):
    for child in _children:
        try:
            log("Sending %s to %s" % (sign, child))
            os.kill(child, sign)
        except:
            pass

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
    log("Executing " + str(components))
    proc = subprocess.Popen(components, stdout=subprocess.PIPE)
    _children.append(proc.pid)
    return proc.stdout

# run a command and return its stdout as a string
def command(*components):
    return command_stream(*components).read()

# fork-run the given function after <delay> seconds
# name is used for log files
def run_fork(name, function, delay=0):
    child_pid = os.fork()
    if child_pid is 0:
        log_dir = path.join(source_dir, "log")
        flags = os.O_CREAT | os.O_WRONLY | os.O_TRUNC
        f = name # + "_" + str(os.getpid())
        os.dup2(os.open(path.join(log_dir, f + ".out"), flags), 1)
        os.dup2(os.open(path.join(log_dir, f + ".err"), flags), 2)
        log("Output redirected")
        setproctitle.setproctitle(setproctitle.getproctitle() + " > " + name)
        try:
            time.sleep(delay)
            function()
        except:
            traceback.print_exc()
        sys.exit(0)
    _children.append(child_pid)
    return child_pid

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
                    thread.sleep(1)
                    os.kill(pid, signal.SIGKILL)
                # try kill too after 1s
                run_thread("kill_" + name, kill_final)
            except:
                pass
    child_pid = run_fork(name, function, delay=delay)
    with open(pid_file, "w") as fd:
        fd.write(str(child_pid))

# log a message, print replacement that works with forked instances
def log(msg, err=False):
    chan = 1
    if err:
        chan = 2
    os.write(chan, msg + "\n")
