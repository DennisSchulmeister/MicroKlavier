# µKlavier - Digital audio synthesizer made with Micropython
# Copyright © 2022  Dennis Schulmeister-Zimolong <dennis@zimolong.eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

"""
Basic utilities for the build script.
"""

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

        class MyCommand extends Command:
            """"""
            $usage$ [command] [-v] [-o out file] in file

            Long help text, possibly spanning multiple paragraphs. Will be used
            as the help text of the command. Thus should not use any markup,
            since it will be printed literally on the console.

            $usage$ will the replaced by the prefix which invokes the command like
            `./Make.py build firmware`.
            """"""
            group      = "build"
            command    = "firmware"
            help_short = "One-line description of the command"
            
            def execute(self, program: str, arguments: List[str]) -> None:
                # Execute the requested actions. The following parameters are given:
                #
                #  * `program`: Name of the executable (usually "./Main.py")
                #  * `arguments`: String list of the CLI arguments to the command
                raise CommandError("Sorry, but I cannot do this.")
    """

    # Registered groups and commands
    groups: ClassVar[Dict[str, Dict[str, CommandDescriptor]]] = {}

    def __init__subclass__(cls) -> None:
        """
        Automatically register the sub-class as a new command.
        """
        if not cls.group in Command.groups:
            Command.groups[cls.group] = {}

        group = Command.groups[cls.group]

        group[cls.command] = CommandDescriptor(
            cls        = cls,
            help_short = cls.help_short if cls.help_short else "[Short description missing]",
            help_long  = dedent(cls.__doc__) if cls.__doc__ else "This command has no help text.",
        )

    # Attributes to be overwritten by sub-classes
    group: ClassVar[str]      = ""
    command: ClassVar[str]    = ""
    help_short: ClassVar[str] = ""
    
    def execute(self, program: str, arguments: List[str]) -> None:
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