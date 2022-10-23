Testing MIDI Input/Output on the PyBoard
========================================

Description
-----------

This is a simple sketch to test that MIDI Input and Output is working
on the PyBoard prototype hardware. For this the hardware must be hooked
up as described in the top-level README file.

All MIDI Input on Pin Y9 is printed to the serial console and mirrored
to the MIDI Output on Pin Y10. If the MIDI Event is a Note On or Note Off
it will be transposed +12 semitones.

Learnings
---------

Implementing this test has been very helpful in better understand some
quirks of MicroPython.

The first lesson was on implementing a static buffer strategy that is not
constantly allocating memory on the heap, mostly by avoiding implicit creation
of new `memoryview` objects each time new data arrives. Even though a `memoryview`
is supposed to be only four machine words in size (according to the MicroPython
source code in py/objarray.c) it still fills the heap sooner or later, causing
irregular garbage collection runs.

The second, maybe even more important, lesson was that MicroPython has some
subtle differences in the `UART` class of each port. For stable timing we
need an interrupt when new MIDI data arrives. But this is only available on
the WyPi port. The documentation contains the class `machine.UART` which
doesn't exist in the MicroPython source, and the class `pyb.UART` which
seems to be mapped to `machine.UART`. Even the documentation is slightly
different.

Thirdly, even with the Viper code emitter, functions, variables, attributes,
methods, ... are still looked up at runtime. Calling a non-existing function
will thus only be noticed during testing. This also means, there is still a
dictionarly look-up executed, costing some runtime.

Fourth, when testing on a breadboard, often times some received bits would
flip. This always occurs at the end of multiple ones, where the next bit
is wrongly detected as one instead of zero. This could be a timing issue with
the circuit components or some random inductance on the breadboard and needs
to be further analyzed.