import sys
import time
import threading

import taurus
from taurus.core.tango import TangoDevice

import PyTango


DEV_NAME_PATTERN = "test/pydsexp/{}"


def registerExtensions():
    factory = taurus.Factory()
    factory.registerDeviceClass("PyDsExp", TaurusPyDsExp)


class TaurusPyDsExp(TangoDevice):

    def __init__(self, name, **kwargs):
        self.call__init__(TangoDevice, name, **kwargs)
        self.my_state = self.getAttribute("state")


class JobThread(threading.Thread):

    def __init__(self, dev=None):
        super(JobThread, self).__init__()
        self.dev = dev

    def run(self):
        for i in range(100):
            if self.dev and self.dev._stop_flag:
                break
            print('In job; {} iteration'.format(i))
            for nb_dev in range(1, 5):
                dev = taurus.Device(DEV_NAME_PATTERN.format(nb_dev))
                dev["attr1"]
            time.sleep(.01)
        if self.dev:
            self.dev.set_state(PyTango.DevState.ON)


class PyDsExpClientClass(PyTango.DeviceClass):

    cmd_list = {'Start': [[PyTango.ArgType.DevVoid, ""],
                          [PyTango.ArgType.DevVoid, ""]],
                'Stop': [[PyTango.ArgType.DevVoid, ""],
                         [PyTango.ArgType.DevVoid, ""]]}

    def __init__(self, name):
        PyTango.DeviceClass.__init__(self, name)
        self.set_type("TestDevice")


class PyDsExpClient(PyTango.Device_4Impl):

    def __init__(self, cl, name):
        PyTango.Device_4Impl.__init__(self, cl, name)
        self.info_stream('In PyDsExpClient.__init__')
        PyDsExpClient.init_device(self)

    @PyTango.DebugIt()
    def init_device(self):
        self._stop_flag = False
        self._thread = None
        self.set_state(PyTango.DevState.ON)

    @PyTango.DebugIt()
    def delete_device(self):
        if self._thread:
            self._stop_flag = True
            self._thread.join()

    @PyTango.DebugIt()
    def is_Start_allowed(self):
        return self.get_state() == PyTango.DevState.ON

    @PyTango.DebugIt()
    def Start(self):
        if self._thread and self._thread.isAlive():
            self.debug_stream('Thread is still alive. Execute Stop command!')
            PyTango.Except.throw_exception(
                'Busy',
                'The previous command execution is still running',
                'Start')
        else:
            self.set_state(PyTango.DevState.MOVING)
            self._stop_flag = False
            self.debug_stream('Starting thread...')
            self._thread = JobThread(self)
            self._thread.start()
        return

    @PyTango.DebugIt()
    def is_Stop_allowed(self):
        return self.get_state() == PyTango.DevState.MOVING

    @PyTango.DebugIt()
    def Stop(self):
        self._stop_flag = True
        self._thread.join()


if __name__ == '__main__':
    registerExtensions()
    util = PyTango.Util(sys.argv)
    util.add_class(PyDsExpClientClass, PyDsExpClient)

    U = PyTango.Util.instance()
    U.server_init()
    U.server_run()
