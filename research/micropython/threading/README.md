Usage of the `_threading` module
================================

Description
-----------

Since the class `pyb.UART` notoriously lacks interrupt handlers
(despite `machine.UART` documenting such a facility for the WiPy port),
we need to find another way to receive MIDI data from UART in a timely
manner without sacrifice of the real-time audio DSP running in parallel.

According to the MicroPython documentation there is support for CPython's
native thread library `_threading`. But as of 10/2022 the API is neither
stable nor documented. See: https://docs.micropython.org/en/latest/library/_thread.html

Thus this is a simple to test to see if a high-priority background thread
can be created, which in the real application would query the UART and call
a callback function to pass the data to the main loop.

Learnings
---------

It doesn't work. The module `_thread` is not available for the PyBoard,
because MICROPY_PY_THREAD defined as 0 in `ports/stm32/mpconfigport.h`.