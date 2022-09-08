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

# Global imports needed by the main scripts
import sys
from make.base import Command, CommandError

# Command registration (by importing the containing modules here)
import make.help
#from make.help import HelpCommand
#HelpCommand.__init__subclass__(HelpCommand)

if __name__ == "__main__":
    program = sys.argv[0]
    group      = ""
    command    = ""
    arguments  = []
    descriptor = None

    if len(sys.argv) >= 3:
        group     = sys.argv[1]
        command   = sys.argv[2]
        arguments = sys.argv[2:]

        try:
            descriptor = Command.groups[group][command]
        except KeyError:
            pass
    
    if not descriptor and len(sys.argv) >= 2:
        try:
            group      = ""
            command    = sys.argv[1]
            descriptor = Command.groups[""][command]
        except KeyError:
            pass
    
    if not descriptor:
        if len(sys.argv) == 1:
            print(f"Usage: {program} [group] command [arguments...]")
            print("See help command for more details.")
            sys.exit(0)
        else:
            raise CommandError("Unknown command. Please try again.")
    
    command_object = descriptor.cls()
    command_object.execute(program, arguments)