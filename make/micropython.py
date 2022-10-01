# µKlavier - Digital audio synthesizer made with MicroPython
# Copyright © 2022  Dennis Schulmeister-Zimolong <dennis@zimolong.eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

"""
Commands to fetch and manage external MicroPython.
"""

from __future__ import annotations

import os, platform, sys

from configparser import ConfigParser
from dataclasses import dataclass
from subprocess import CalledProcessError
from typing import List

from .base import Command
from . import utils

@dataclass
class CommandLineOptions:
    """
    Parsed command line arguments with default values.
    """
    port: str  = ""
    board: str = ""
    lto: str   = ""

    @classmethod
    def parse(cls, config: ConfigParser, arguments: List[str]) -> CommandLineOptions:
        """
        Parses the given list of command line arguments and creates a new
        object instance with all recognized values.
        """
        options = CommandLineOptions()

        options.port  = config["micropython"]["port"]
        options.board = config["micropython"]["board"]
        options.lto   = config["micropython"]["lto"]

        for argument in arguments:
            if argument.startswith("port="):
                options.port = argument.split("port=")[1].strip()
            elif argument.startswith("board="):
                options.board = argument.split("board=")[1].strip()
            elif argument.startswith("lto="):
                options.lto = argument.split("lto=")[1].strip()
        
        return options

class MicroPythonFetchCommand(Command, group="micropython", command="fetch"):
    """
    Fetch MicroPython source tree needed to build the application
    $usage$

    This clones the MicroPython git repository into build/micropython, to make
    it available for all sub-sequent commands. Beware that the directory is
    always deleted first, which will make you loose any local modifications or
    previously built MicroPython images.
    """

    def execute(self) -> None:
        utils.print_box("Cloning MicroPython git repository")
        utils.rmtree(self.config["micropython"]["target_dir"])
        utils.makedirs(self.config["micropython"]["target_dir"])

        utils.git_clone(
            git_url    = self.config["micropython"]["git_url"],
            target_dir = self.config["micropython"]["target_dir"],
            commit     = self.config["micropython"]["commit"],
        )

class MicroPythonDeleteCommand(Command, group="micropython", command="delete"):
    """
    Delete previously fetched MicroPython source tree
    $usage$

    This simply deletes the build/micropython directory, where the external
    source tree and built images for MicroPython are stored.
    """

    def execute(self) -> None:
        utils.print_box("Delete external MicroPython source tree")
        utils.rmtree(self.config["micropython"]["target_dir"])

class MicroPythonBuildCommand(Command, group="micropython", command="build"):
    """
    Build the MicroPython interpreter and tools for local execution.
    $usage$

    This builds the MicroPython interpreter for the host system as well
    as all tools included in the MicroPython source tree, including among
    others ”mpy-cross” which is used for compiling Python code into native
    code of the micro controller.
    """

    def execute(self) -> None:
        old_cwd = os.getcwd()
        new_cwd = utils.get_micropython_dir(self.config)
        cross_compile = "CROSS_COMPILE="

        if platform.system() == "Windows":
            if sys.maxsize > 2**32:
                # 64-bit Windows
                cross_compile += "x86_64-w64-mingw32-"
            else:
                # 32-bit Windows
                cross_compile += "i686-w64-mingw32-"

        utils.chdir(new_cwd)
        utils.run(["make", "submodules"])
        utils.run(["make", "deplibs", cross_compile])
        utils.run(["make", cross_compile])
        utils.run(["make", "-C", "../../mpy-cross", cross_compile])
        utils.chdir(old_cwd)

class MicroPythonImageCommand(Command, group="micropython", command="image"):
    """
    Build a MicroPython firmware image to be flashed onto a device
    $usage$ [port=$config:micropython:port$] [board=$config:micropython:board$] [lto=$config:micropython:lto$]

    This switches to the requested ports directory inside the MicroPython source tree
    and calls `make` to build a firmware image. By default an image of the stm32 port
    for the PyBoard 1.1 is built with link time optimization to reduce the image size
    a little.

    If building for any other board, you might need to manually perform additional
    build steps from inside the ports directory. e.g. the README file for the stm32
    port mentions, that some boards require a boot loader called “mboot” to be built
    and flashed before MicroPython can be flashed.
    """

    def execute(self) -> None:
        options = CommandLineOptions.parse(self.config, self.arguments)

        old_cwd = os.getcwd()
        utils.chdir(self.config["micropython"]["target_dir"] + f"/ports/{options.port}")
        utils.run(["make", "submodules"])
        utils.run(["make", f"BOARD={options.board}", f"LTO={options.lto}"])
        utils.chdir(old_cwd)

class MicroPythonDeployCommand(Command, group="micropython", command="deploy"):
    """
    Flash a previously built micropython firmware image
    $usage$ [port=$config:micropython:port$] [board=$config:micropython:board$]

    This calls `make deploy` in the corresponding port directory of MicroPython
    to flash a previously built image to a board.
    """

    def execute(self) -> None:
        options = CommandLineOptions.parse(self.config, self.arguments)

        old_cwd = os.getcwd()
        utils.chdir(self.config["micropython"]["target_dir"] + f"/ports/{options.port}")
        utils.run(["make", "deploy", f"BOARD={options.board}"])
        utils.chdir(old_cwd)

class MicroPythonCleanCommand(Command, group="micropython", command="clean"):
    """
    Clean all build files inside the MicroPython source tree
    $usage$

    This recursively calls `make clean` in all directories of MicroPython that
    contain a Makefile.
    """

    def execute(self) -> None:
        old_cwd = os.getcwd()

        root_dir = self.config["micropython"]["target_dir"]
        found_dirs = [os.path.abspath(root) for root, dirs, files in os.walk(root_dir) if "Makefile" in files]

        for dir in found_dirs:
            utils.chdir(dir)

            try:
                utils.run(["make", "clean"])
            except CalledProcessError:
                pass
        
        utils.chdir(old_cwd)
