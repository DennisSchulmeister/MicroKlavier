# µKlavier - Digital audio synthesizer made with Micropython
# Copyright © 2022  Dennis Schulmeister-Zimolong <dennis@zimolong.eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

"""
General commands that belong to no group.
"""

from .base import Command, CommandError
from typing import List

class HelpCommand(Command, group="", command="help"):
    """
    Display help page of this script or one of its commands
    $usage$ [<group>] [<command>]
    
    See Dilbert strip from August 15, 2000: Our disaster recovery plan is to
    panic and cry 'Help! Help!'. Obviously some disaster just happened or you
    are simply curious how to use this script. This page is here to help.

    This is the help page for the help command. So you already know, how to
    get help for a specific command. Each command comes with its own help
    page that can be retrieved with '$program$ help <group> <command>' or
    just '$program$ help <command>', if the command belongs to no group.
    """

    def execute(self) -> None:
        """
        Run the command.
        """
        match self.arguments:
            case [command]:
                self._display_help("", command)
            case [group, command]:
                self._display_help(group, command)
            case []:
                self._display_summary()
            case _:
                raise CommandError("Too many arguments given. Please specify group and/or command only.")

    def _display_summary(self) -> None:
        """
        Show a summary page with a list of all groups, commands and their short description.
        """
        print(f"Usage: {self.program} [<group>] <command> [<arguments...>]")
        print("")
        print("Supported groups and commands:")

        maxlen = 0
        for group in Command.groups.keys():
            for command in Command.groups[group].keys():
                maxlen = max(maxlen, len(group) + len(command) + 1)

        for group in Command.groups.keys():
            print("")

            for command in Command.groups[group]:
                full_command = f"{group} {command}".strip()
                print(f"  {full_command.ljust(maxlen)}    " + Command.groups[group][command].help_short)
    
    def _display_help(self, group: str, command: str) -> None:
        """
        Show detailed help page for the given command.
        """
        space = " " if group and command else ""

        try:
            help_text = Command.groups[group][command].help_long
            help_text = help_text.replace("$usage$", f"Usage: {self.program} {group}{space}{command}")
            help_text = help_text.replace("$program$", self.program)

            for section in self.config.sections():
                for key in self.config[section]:
                    help_text = help_text.replace(f"$config:{section}:{key}$", self.config[section][key])
                    
            print(help_text)
        except ValueError:
            raise CommandError(f"Unknown command. Please try again.")
