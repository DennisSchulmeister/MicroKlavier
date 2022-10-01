Tests, Experiments and Benchmarks
=================================

This directory contains different experiments that are not part of the
application itself. As many experiments target especially MicroPython or
regular Python, there is a sub-directory for each runtime, which in turn
contain one directory per experiment.

Building the experiments with make.py
-------------------------------------

The experiments can be built by running the following command from the
root level of the project:

``sh
./make.py research build
```

Optionally only the MicroPython or Python experiments can be built with:

``sh
./make.py research build micropython
./make.py research build python
```

Or just a single experiment:

``sh
./make.py research build micropython/main-native-code
```

For MicroPython this compiles all source files to *.mpy-Files and moves them
to `build/experiments/micropython/...`. For Python this copies the sources
verbatim to `build/experiments/python/...`, as they don't need to be compiled.

Custom build steps for an experiment
------------------------------------

Experiments can include a file called `_build.py` for custom build steps.
It will be executed as a script after the sources have been copied but before
the Python sources are compiled. The working directory will be set to the
target directory `build/experiments/...`.

Custom dependencies for an experiment
-------------------------------------

If an experiment contains a file called `requirements.txt`, this will be
used to install foreign libraries via pip (Python) or upip (MicroPython)
during the build.