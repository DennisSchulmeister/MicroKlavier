#! /bin/env python

# µKlavier - Digital audio synthesizer made with Micropython
# Copyright © 2022  Dennis Schulmeister-Zimolong <dennis@zimolong.eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

"""
Build script to automate the most common actions like pulling libraries,
compiling and flashing the firmware image and compiling application code.
"""

# Global imports needed by the main script
import os, sys, traceback

from make.base import main
from make.utils import print_error

# Command registration by importing the containing modules here.
# Note, that import order determines the order of the command
# groups in the help summary! Also, the order in which the classes
# are defined in the modules determines their order in the help
# summary. This allows to provide the list in a logical order,
# e.g. putting the command to fetch external dependencies before
# the command to build the source code.
import make.general
import make.micropython
import make.app

if __name__ == "__main__":
    try:
        # Always use the project root as the initial working directory!
        os.chdir(os.path.dirname(__file__))

        # Run the requested command
        main()
    except BaseException as ex:
        (ex_type, ex_value, ex_traceback) = sys.exc_info()

        print("")
        print_error(f"{ex_type.__name__}: {ex}")
        traceback.print_tb(ex_traceback)