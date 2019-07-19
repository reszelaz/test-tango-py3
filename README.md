# test-tango-py3

Examples to reproduce problem with unsubscribe of attributes
in `__del__` using Python 3. One example assumes using Taurus 4.5. Another
example assumes using PyTango 9.2.5 and higher. 

In order to reproduce the problem:
1. Register in Tango Database:
  * PyDsExp DS with instance name `test` with 4 devices of PyDsExp class with 
    the following names: `test/pydsexp/1`, `test/pydsexp/2`, `test/pydsexp/3` and 
    `test/pydsexp/4`
  * PyDsExpClient DS with instance name `test` with 1 device of PyDsExpClient 
  class with name: `test/pydsexpclient/1`
2. Start PyDsExp: `python PyDsExp.py test`
3. Start PyDsExpClient (either from taurus or from pytango directory): `python 
   PyDsExpClient.py test`
4. Call Start command of PyDsExpClient device.
5. Wait...

We couldn't reproduce the problem using a simple client instead of 
PyDsExpClient DS.

Also the following problem does not happen with Python 2. Most probably this
has to do with the improvements in Python 3 garbage collection and its calls
to `__del__`. 
