import time

from PyDsExpClient import JobThread


_thread = JobThread()
_thread.start()
while _thread.isAlive():
    time.sleep(0.01)
_thread.join()
