Native Code in Main Script
==========================

Maybe a trivial thing, but this experiment tries to replace the `main.py` script
in the PyBoard's flash with a pre-compiled `main.mpy` containing native code.

Procedure
---------

 1. Run `make` to compile.
 2. Plug-in PyBoard to the host computer.
 3. Delete or rename the `main.py` file on the PyBoard.
 4. Copy the compiled `main.mpy` file to the PyBoard.
 5. Restart PyBoard.

Expected Result
---------------

The blue LED should blink and the REPL not be available during that time.
