# µKlavier - Digital audio synthesizer made with Micropython
# Copyright © 2022  Dennis Schulmeister-Zimolong <dennis@zimolong.eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

"""
Base classes to define and register commands for the build script.
"""

import glob, os, sys

from configparser import ConfigParser
from dataclasses import dataclass
from textwrap import dedent
from typing import ClassVar, Dict, ForwardRef, List

@dataclass
class CommandDescriptor:
    """
    Data class used by the main script to identify all commands and their help texts.
    An instance of this class will be created for each command sub-class and be stored
    in `Command.groups` in a two-level dictionary `group -> command -> CommandDescriptor`.
    """
    cls: ForwardRef("Command")
    help_short: str
    help_long: str

class Command:
    """
    Parent class for an executable commend to be called with `./Make.py command`.
    By making each command an instance of this class, common logic like passing
    parameters of building a help page can be simplified.
    
    A command can be defined like this:

    .. code-block:: python
        from .base import Command, CommandError
        from typing import List

        class MyCommand(Command, group="build", command="firmware"):
            """"""
            One-line description of the command
            $usage$ [board=$config:micropython:board$] <filename...>

            Long help text, possibly spanning multiple paragraphs. Will be used
            as the help text of the command. Thus should not use any markup,
            since it will be printed literally on the console.

            $usage$ will the replaced by the prefix which invokes the command like
            `./Make.py build firmware`.

            $config:…$ will be replaces with a configuration value from `make.conf`,
            specifying the section and key to be read.
            """"""

            def execute(self) -> None:
                # Execute the requested actions.
                raise CommandError("Sorry, but I cannot do this.")
    
    It is important to contain a doc string with the help text of the command.
    The first line will be used as a one-line summary. The remainder as the
    full help page. The object will contain the following attributes:

     * `self.program`: Name of the executable (usually "./Main.py")
     * `self.arguments`: String list of the CLI arguments to the command
     * `self.config`: `ConfigParser` object with the content of `make.conf`
    """

    # Registered groups and commands
    groups: ClassVar[Dict[str, Dict[str, CommandDescriptor]]] = {}

    def __init_subclass__(cls, group: str, command: str, **kwargs) -> None:
        """
        Automatically register the sub-class as a new command.
        """
        super().__init_subclass__(**kwargs)

        if not group in Command.groups:
            Command.groups[group] = {}

        group = Command.groups[group]
        help_long = dedent(cls.__doc__).strip() if cls.__doc__ else "This command has no help text."
        help_short = help_long.splitlines()[0]

        group[command] = CommandDescriptor(
            cls        = cls,
            help_short = help_short,
            help_long  = help_long,
        )
    
    def __init__(self, program: str, arguments: List[str]):
        """
        Constructor to initialize the common object attributes.
        """
        # Read configuration and resolve glob patters in its keys
        config = ConfigParser()
        config.read("make.conf")

        for category in config:
            for key in config[category]:
                if not key.startswith("./"):
                    continue
            
                value = config[category][key]
                del config[category][key]

                for new_key in glob.glob(key.replace("/", os.path.sep)):
                    if os.path.isdir(new_key):
                        new_key = new_key.replace(os.path.sep, "/")
                        config[category][new_key] = value
        
        # Initialize common attributes
        self.program   = program
        self.arguments = arguments
        self.config    = config

    def execute(self) -> None:
        """
        Abstract method to be overwritten by sub-classes to actually execute
        the command. `program` is the executable name of the script, which should
        not be needed by many commands. `arguments` is a string list of all CLI
        arguments to the command.

        Errors should be raised as `CommandError` exceptions. Otherwise the script
        will exit with return code 0.
        """
        pass

class CommandError(Exception):
    """
    Exception to be used by Command sub-classes to abort execution with an error message.
    """
    pass


def main():
    """
    Main function of the build script. Parses the CLI arguments to find the
    right class to execute the requested command. Returns nothing on success
    or throws an exception on errors.
    """
    program    = sys.argv[0]
    group      = ""
    command    = ""
    arguments  = []
    descriptor = None

    if len(sys.argv) >= 3:
        group = sys.argv[1]
        command = sys.argv[2]
        arguments = sys.argv[3:]

        try:
            descriptor = Command.groups[group][command]
        except KeyError:
            pass

    if not descriptor and len(sys.argv) >= 2:
        try:
            group = ""
            command = sys.argv[1]
            arguments = sys.argv[2:]
            descriptor = Command.groups[""][command]
        except KeyError:
            pass

    if not descriptor:
        if len(sys.argv) == 1:
            print(f"Usage: {program} [<group>] <command> [<arguments...>]")
            print("See help command for more details.")
            return
        else:
            raise CommandError("Unknown command. Please try again.")

    command_object = descriptor.cls(program, arguments)
    command_object.execute()
