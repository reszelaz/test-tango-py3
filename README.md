# test-tango-py3

Examples to reproduce problem with unsubscribe of attributes
in `__del__` using Python 3. One example we are using Taurus 4.5. In the other
one we just use the PyTango 9.2.5 (or higher).

The architecture is as following. We have:
* first DS with a Tango device with two attributes: `state` and `attr1`.
* second DS with a Tango device which in its implementation instantiate two Python classes:
  * a `DeviceProxy` wrapper to the device from the first DS
  * an attribute which in its constructor subscribes to configuration events and
    in its destructor unsubscribes from these events.

To my knowledge the second DS crashes by an unhandled exception in the Tango `EventConsumerKeepAliveThread` (`DelayEvent` constructor). Most probably this is somehow related to the garbage collector calls to the destructor of the attribute Python class.

The core dump stack:

```
(gdb) bt full
#0  __GI_raise (sig=sig@entry=6) at ../sysdeps/unix/sysv/linux/raise.c:51
        set = {__val = {18446744066192564231, 77309411330, 0, 139755407532264, 0, 0, 4916306193379385684, 7234307576299943525, 139755407535872, 139755407535920, 139755407536120, 0, 139755407536136, 0, 0, 0}}
        pid = <optimized out>
        tid = <optimized out>
#1  0x00007f1bd09a642a in __GI_abort () at abort.c:89
        save_stage = 2
        act = {__sigaction_handler = {sa_handler = 0x7f1b28009aa0, sa_sigaction = 0x7f1b28009aa0}, sa_mask = {__val = {139757444187424, 2, 139757364585732, 2, 2, 139757444170816, 139757440880494, 139757444187424, 2, 139757364585732, 139754611972672, 2, 139754611972672, 
              139754611972768, 1, 139754611972448}}, sa_flags = -871906624, sa_restorer = 0x7f1bd0d0c6e0 <stderr>}
        sigs = {__val = {32, 0 <repeats 15 times>}}
#2  0x00007f1bcc07f0ad in __gnu_cxx::__verbose_terminate_handler() () from /usr/lib/x86_64-linux-gnu/libstdc++.so.6
No symbol table info available.
#3  0x00007f1bcc07d066 in ?? () from /usr/lib/x86_64-linux-gnu/libstdc++.so.6
No symbol table info available.
#4  0x00007f1bcc07d0b1 in std::terminate() () from /usr/lib/x86_64-linux-gnu/libstdc++.so.6
No symbol table info available.
#5  0x00007f1bcc07d2c9 in __cxa_throw () from /usr/lib/x86_64-linux-gnu/libstdc++.so.6
No symbol table info available.
#6  0x00007f1bcec36ab5 in Tango::Except::throw_exception (reason=<optimized out>, desc=<optimized out>, origin=<optimized out>, sever=<optimized out>) at /usr/include/tango/except.h:135
        errors = {<_CORBA_Unbounded_Sequence<Tango::DevError>> = {<_CORBA_Sequence<Tango::DevError>> = {pd_max = <optimized out>, pd_len = <optimized out>, pd_rel = true, pd_bounded = <optimized out>, pd_buf = 0x7f1b28009938}, <No data fields>}, <No data fields>}
#7  0x00007f1bce1ca1cd in Tango::TangoMonitor::get_monitor (this=0x55717a14f590) at ../../../lib/cpp/server/tango_monitor.h:150
        interupted = <optimized out>
        th = 0x55717951f880
        synchronized = {mutex = @0x55717a14f590}
#8  0x00007f1bce1e89b0 in Tango::DelayEvent::DelayEvent (this=0x7f1b576bed30, ec=<optimized out>) at zmqeventconsumer.cpp:3813
        sender = {ptr = 0x7f1b280008c0}
        buffer = {6 '\006', <optimized out>, <optimized out>, <optimized out>, <optimized out>, <optimized out>, <optimized out>, <optimized out>, <optimized out>, <optimized out>}
        length = 1
        send_data = {msg = {_ = "\000\000\000\000\000\000\000\000\a\354kW\033\177\000\000 \354kW\033\177\000\000`\352kW\033\177\000\000\300\343\002\200\033\177\000\000`\000\000\000\000\177\000\000\320\024\000(\033\177\000\000\330\310\034\316\000\000\000"}}
        reply = {msg = {_ = "\000\000\000\000\000\000\000\000OK", '\000' <repeats 32 times>, "e", '\000' <repeats 20 times>}}
        str = "ZmqEventSubscriptionChange"
#9  0x00007f1bce1d4991 in Tango::EventConsumerKeepAliveThread::run_undetached (this=0x55717951f880, arg=<optimized out>) at eventkeepalive.cpp:

        de = {released = false, eve_con = 0x55717a14ede0}
        time_to_sleep = 10
        now = 1563356831
        event_consumer = 0x55717a14ede0
        notifd_event_consumer = 0x0
        time_left = <optimized out>
        exit_th = false
#10 0x00007f1bcc8176c1 in omni_thread_wrapper () from /usr/lib/libomnithread.so.3
No symbol table info available.
#11 0x00007f1bd18674a4 in start_thread (arg=0x7f1b576bf700) at pthread_create.c:456
        __res = <optimized out>
        pd = 0x7f1b576bf700
        now = <optimized out>
        unwind_buf = {cancel_jmp_buf = {{jmp_buf = {139755407537920, -4371207478120532088, 140720643802702, 140720643802703, 139755399147520, 3, 4422806561858533256, 4423092259558406024}, mask_was_saved = 0}}, priv = {pad = {0x0, 0x0, 0x0, 0x0}, data = {prev = 0x0, 
              cleanup = 0x0, canceltype = 0}}}
        not_first_call = <optimized out>
        pagesize_m1 = <optimized out>
        sp = <optimized out>
        freesize = <optimized out>
        __PRETTY_FUNCTION__ = "start_thread"
#12 0x00007f1bd0a5ad0f in clone () at ../sysdeps/unix/sysv/linux/x86_64/clone.S:97
No locals.
```

In order to reproduce the problem:
1. Register in Tango Database:
  * PyDsExp DS with instance name `test` with 4 devices of PyDsExp class with 
    the following names: `test/pydsexp/1`, `test/pydsexp/2`, `test/pydsexp/3` and 
    `test/pydsexp/4`:
    ```console
    tango_admin --add-server PyDsExp/test PyDsExp test/pydsexp/1,test/pydsexp/2,test/pydsexp/3,test/pydsexp/4    
    ```
  * PyDsExpClient DS with instance name `test` with 1 device of PyDsExpClient 
    class with name: `test/pydsexpclient/1`:
    ```console
    tango_admin --add-server PyDsExpClient/test PyDsExpClient test/pydsexpclient/1
    ```
  
2. Start PyDsExp: `python3 PyDsExp.py test`
3. Start PyDsExpClient (either from taurus or from pytango directory): `python3 PyDsExpClient.py test`
4. Call Start command of PyDsExpClient device.
5. Wait...

We couldn't reproduce the problem using a simple client instead of 
PyDsExpClient DS.

Also the following problem does not happen with Python 2. Most probably this
has to do with the improvements in Python 3 garbage collection and its calls
to `__del__`. 
