import sys
import time
import weakref
import threading

import PyTango


DEV_NAME_PATTERN = "test/pydsexp/{}"


def CallableRef(object, del_cb=None):
    """This function returns a callable weak reference to a callable object.
    Object can be a callable object, a function or a method.

    :param object: a callable object
    :type object: callable object
    :param del_cb: calback function. Default is None meaning to callback.
    :type del_cb: callable object or None

    :return: a weak reference for the given callable
    :rtype: BoundMethodWeakref or weakref.ref"""
    im_self = None
    if hasattr(object, '__self__'):
        im_self = object.__self__
    elif hasattr(object, 'im_self'):
        im_self = object.im_self

    if im_self is not None:
        return BoundMethodWeakref(object, del_cb)
    return weakref.ref(object, del_cb)


class BoundMethodWeakref(object):
    """This class represents a weak reference to a method of an object since
    weak references to methods don't work by themselves"""

    def __init__(self, bound_method, del_cb=None):
        cb = (del_cb and self._deleted)
        self.func_ref = weakref.ref(bound_method.__func__, cb)
        self.obj_ref = weakref.ref(bound_method.__self__, cb)
        if cb:
            self.del_cb = CallableRef(del_cb)
        self.already_deleted = 0

    def _deleted(self, obj):
        if not self.already_deleted:
            del_cb = self.del_cb()
            if del_cb is not None:
                del_cb(self)
                self.already_deleted = 1

    def __call__(self):
        obj = self.obj_ref()
        if obj is not None:
            func = self.func_ref()
            if func is not None:
                return func.__get__(obj)

    def __hash__(self):
        return id(self)

    def __cmp__(self, other):
        if other.__class__ == self.__class__:
            from past.builtins import cmp
            ret = cmp((self.func_ref, self.obj_ref),
                      (other.func_ref, other.obj_ref))
            return ret
        return 1

    def __eq__(self, other):
        if hasattr(other, 'func_ref') and hasattr(other, 'obj_ref'):
            return ((self.func_ref, self.obj_ref)
                    == (other.func_ref, other.obj_ref))
        return False

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        obj, func = self.obj_ref(), self.func_ref()
        return 'BoundMethodWeakRef of %s.%s' % (obj, func)


# Reimplementation of BoundMethodWeakref class to avoid to have a hard
# reference in the event callbacks.
# Related to "Keeping references to event callbacks after unsubscribe_event"
# PyTango #185 issue.
class _BoundMethodWeakrefWithCall(BoundMethodWeakref):

    def __init__(self, bound_method, del_cb=None):
        """ Reimplementation of __init__ method"""
        super(_BoundMethodWeakrefWithCall, self).__init__(bound_method,
                                                          del_cb=del_cb)
        self.__name__ = self.func_ref().__name__

    def __call__(self, *args, **kwargs):
        """ Retrieve references and call callback with arguments
        """
        obj = self.obj_ref()
        if obj is not None:
            func = self.func_ref()
            if func is not None:
                return func(obj, *args, **kwargs)


class PyTangoDevice:

    def __init__(self, name):
        print("PyTangoDevice.__init__")
        self._name = name
        self.dp = PyTango.DeviceProxy(name)
        self._state = self.getAttribute("state")

    def getAttribute(self, name):
        return PyTangoAttribute(name, self)


class PyTangoAttribute:

    def __init__(self, name, dev):
        print("PyTangoAttribute.__init__")
        self._ids = []
        self._name = name
        self._dev = dev
        for type_ in [PyTango.EventType.ATTR_CONF_EVENT]:
            cb = _BoundMethodWeakrefWithCall(self.push_event)
            # print("PyTangoAttribute.__init__: before subscribe", self._name)
            id_ = self._dev.dp.subscribe_event(name, type_, cb)#, [], True)
            # print("PyTangoAttribute.__init__: after subscribe", self._name)
            self._ids.append(id_)

    def __del__(self):
        print("PyTangoAttribute.__del__")
        while len(self._ids):
            id_ = self._ids.pop()
            # print("PyTangoAttribute.__del__: before unsubscribe", self._name)
            self._dev.dp.unsubscribe_event(id_)
            # print("PyTangoAttribute.__del__: after unsubscribe", self._name)

    def push_event(self, _):
        print("PyTangoAttribute.push_event")
        count = 0
        for i in range(100):
            time.sleep(0.001)
            count += 1


class JobThread(threading.Thread):

    def __init__(self, dev=None):
        super(JobThread, self).__init__()
        self.dev = dev

    def run(self):
        for i in range(100):
            print('In job; {} iteration'.format(i))
            for nb_dev in range(1, 5):
                dev = PyTangoDevice(DEV_NAME_PATTERN.format(nb_dev))
                attr = dev.getAttribute("attr1")
                while len(attr._ids):
                    id_ = attr._ids.pop()
                    dev.dp.unsubscribe_event(id_)
            time.sleep(0.01)


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
    util = PyTango.Util(sys.argv)
    util.add_class(PyDsExpClientClass, PyDsExpClient)

    U = PyTango.Util.instance()
    U.server_init()
    U.server_run()
