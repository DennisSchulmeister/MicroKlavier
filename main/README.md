Main application source code
============================

This directory contains the MicroPython source code that runs on the main µC.
This is the actual synthesizer including MIDI communication, note allocation,
tone generation and effects. It can either run stand-alone or connect via a
serial interface to a secondary µC for a physical and graphical user interface.