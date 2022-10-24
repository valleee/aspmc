import signal
import psutil
import os

tempfiles = set()

def handler(signum, frame):
    for name in tempfiles:
        os.remove(name)
    # get pid of own process
    parent_pid = os.getpid()   
    parent = psutil.Process(parent_pid)
    # kill all children
    for child in parent.children(recursive=True):  
        child.kill()
    # kill self
    raise KeyboardInterrupt("Received Control+C, cleaning up and shutting down.")


signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)