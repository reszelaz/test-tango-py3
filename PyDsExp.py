import sys

import PyTango


class PyDsExpClass(PyTango.DeviceClass):

    attr_list = {'attr1': [[PyTango.ArgType.DevLong,
                            PyTango.AttrDataFormat.SCALAR,
                            PyTango.AttrWriteType.READ]]}

    def __init__(self, name):
        PyTango.DeviceClass.__init__(self, name)
        self.set_type("TestDevice")


class PyDsExp(PyTango.Device_4Impl):

    def __init__(self, cl, name):
        PyTango.Device_4Impl.__init__(self, cl, name)
        self.info_stream('In PyDsExp.__init__')
        PyDsExp.init_device(self)

    @PyTango.DebugIt()
    def init_device(self):
        self.info_stream('In Python init_device method')
        self.set_state(PyTango.DevState.ON)

    @PyTango.DebugIt()
    def read_attr1(self, the_att):
        self.info_stream("read_attr1")
        the_att.set_value(0)


if __name__ == '__main__':
    util = PyTango.Util(sys.argv)
    util.add_class(PyDsExpClass, PyDsExp)

    U = PyTango.Util.instance()
    U.server_init()
    U.server_run()
