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

from .base import Command, CommandError
from typing import List

class HelpCommand(Command):
    """
    $usage$ [group] [command]
    
    See Dilbert strip from August 15, 2000: Our disaster recovery plan is to
    panic and cry 'Help! Help!'. Obviously some disaster just happened or you
    are simply curious how to use this script. This page is here to help.

    Without any arguments this help page is displayed. Optionally, the name of
    a group and command can be given to view the specific help page of the
    command, e.g. `build firmware` to see how a firmware image can be built or
    just `help` to get help for the help command.
    """
    group      = ""
    command    = "help"
    help_short = "Display help page of this script or one of its commands"

    def execute(self, program: str, arguments: List[str]) -> None:
        """
        Show the requested help page.
        """
        match arguments:
            case [command]:
                self._display_help(program, "", command)
            case [group, command]:
                self._display_help(program, group, command)
            case []:
                self._display_summary(program)
            case _:
                raise CommandError("Too many arguments given. Please specify group and/or command only.")

    def _display_summary(self, program: str) -> None:
        """
        Show a summary page with a list of all groups, commands and their short description.
        """
        print(f"Usage: {program} [group] command [arguments...]")
        print("Note, that only a few commands don't belong to a group. Most time the group is mandatory.")
        print("")

        maxlen = 0
        for group in Command.groups.keys():
            for command in Command.groups[group].keys():
                maxlen = max(maxlen, len(group) + len(command) + 1)

        i = 0
        for group in sorted(Command.groups.keys()):
            if i:
                print("")
            i += 1

            for command in sorted(Command.groups[group]):
                full_command = f"{group} {command}"
                print(f"  {full_command.ljust(maxlen)}    " + Command.groups[group][command].help_short)
    
    def _display_help(self, program: str, group: str, command: str) -> None:
        """
        Show detailed help page for the given command.
        """
        try:
            help_text = Command.groups[group][command].help_long
            help_text = help_text.replace("$usage$", f"Usage: {program}")
            print(help_text)
        except ValueError:
            raise CommandError(f"Unknown command. Please try again.")
