# µKlavier - Digital audio synthesizer made with Micropython
# Copyright © 2022  Dennis Schulmeister-Zimolong <dennis@zimolong.eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

"""
Commands to build, compile, assemble, ... the various source codes.
"""

from __future__ import annotations, with_statement
from distutils.command.build import build

import os, venv, platform
from configparser import ConfigParser
from dataclasses import dataclass, field
from typing import Dict, List, Type

from .base import Command, CommandError
from . import utils

@dataclass
class SourceBuilder:
    """
    Abstract base-class to describe and perform a build.
    """
    source_dir: str = ""
    build_dir: str = ""
    config: ConfigParser = None
    parameters: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def create(cls: Type[SourceBuilder], config: ConfigParser, arguments: List[str]) -> List[SourceBuilder]:
        """
        Factory method that parses the given command line arguments and creates
        a `SourceBuilder` instance for each source project to be built.
        """
        # Parse command line arguments to recognize any overwritten parameter as
        # well as the project directories that shall be built. Returns a dictionary
        # that maps each project directory to build to a language runtime according
        # to the `make.conf` configuration file.
        build_all   = True
        source_dirs = {}
        parameters  = {}

        for argument in arguments:
            # Recognize configuration parameter
            if "=" in argument:
                key, value = argument.split("=", maxsplit=1)
                parameters[key] = value
                continue

            # At least on directory given, so don't build all projects.
            # Instead find out how to build this specific directory.
            build_all = False
            runtime   = ""
            
            # Skip non-existing directories
            if not os.path.isdir(argument):
                continue

            # Find out runtime for the given directory and whether the directory
            # specifies a single project or a parent directory with many projects
            # to build
            prefix = argument.replace(os.path.sep, "/")
            prefix = prefix[2:] if prefix.startswith("./") else prefix
            prefix = f"{prefix}/" if not prefix.endswith("/") else prefix
            prefix = prefix.replace("/", os.path.sep)
            
            for key in config["app"]:
                if not key.startswith("./"):
                    continue

                source_dir = key[2:]
                source_dir = f"{source_dir}/" if not source_dir.endswith("/") else source_dir
                source_dir = source_dir.replace("/", os.sep)

                if platform.system() == "Windows":
                    # Paths are case-insensitive on Windows
                    prefix = prefix.lower()
                    source_dir = source_dir.lower()
                    
                if source_dir.startswith(prefix):
                    runtime = config["app"][key]
                    source_dirs[source_dir] = runtime

            if not source_dirs:
                raise CommandError(f"No language runtime found for {argument}. Please check make.conf")

            source_dirs[prefix] = runtime
        
        # Build all sub-projects, if none given in the arguments
        if build_all:
            for key in config["app"]:
                if not key.startswith("./"):
                    continue

                runtime = config["app"][key]
                prefix = key[2:].replace("/", os.path.sep)

                source_dirs[prefix] = runtime
        
        # Create one SourceBuilder object per directory, using a different
        # sub-class depending on the detected language runtime
        result = []
        target_dir = config["app"]["target_dir"].replace("/", os.path.sep)

        for prefix in source_dirs.keys():
            runtime = source_dirs[prefix]
            builder_class = None

            match runtime:
                case "python":
                    builder_class = SourceBuilderPython
                case "micropython":
                    builder_class = SourceBuilderMicroPython
                case _:
                    raise CommandError(f"Unknown language runtime {runtime}. Please check make.conf")

            builder = builder_class(
                source_dir = prefix,
                build_dir  = os.path.join(target_dir, prefix),
                config     = config,
                parameters = parameters,
            )

            builder.set_default_parameters()
            result.append(builder)

        return result

    def build(self) -> None:
        """
        Template method that drives the build process. Call this to perform the build.
        It calls into the various `do_...` methods below for concrete actions.
        """
        utils.print_box(f"Building {self.source_dir}")

        utils.rmtree(self.build_dir)
        utils.copytree(self.source_dir, self.build_dir)

        old_cwd = os.getcwd()
        utils.chdir(self.build_dir)

        self.do_prepare_build()

        build_script = "_build.py"

        if os.path.isfile(build_script):
            utils.run(["python", build_script])
            utils.remove(build_script)

        self.do_dependencies()
        self.do_compile()
        self.do_finalize_build()

        utils.chdir(old_cwd)

        utils.print_line("")

    def clean(self) -> None:
        """
        Clean up by deleting the build directory.
        """
        utils.rmtree(self.build_dir)
        
    def set_default_parameters(self):
        """
        Abstract method to set default parameter values from configuration.
        This is meant to provide default values to parameters that could
        be set via command line arguments, without hard-coding the default
        values here.
        """
        pass

    def do_prepare_build(self) -> None:
        """
        Abstract method for initial preparation before the build begins.
        """
        pass

    def do_dependencies(self) -> None:
        """
        Abstract method to setup an environment and install required dependencies.
        """
        pass

    def do_compile(self) -> None:
        """
        Abstract method to perform the actual compilation.
        """
        pass

    def do_finalize_build(self) -> None:
        """
        Abstract method for final cleanup after the build was successfully finished.
        """
        pass

@dataclass
class SourceBuilderPython(SourceBuilder):
    """
    Source builder for regular Python projects running in CPython or similar.
    """
    
    def do_dependencies(self):
        """
        Set up a new virtual Python environment in the `env` sub-directory
        and use `pip` to install dependencies, but only, if the source tree
        declares dependencies in a `requirements.txt` file.
        """
        pip_file = "requirements.txt"

        if not os.path.isfile(pip_file):
            return
        
        venv.create("env", symlinks=True, with_pip=True)
        utils.run(["pip", "install", "--no-input", "--prefix", "env", "-r", pip_file])

@dataclass
class SourceBuilderMicroPython(SourceBuilder):
    """
    Source builder for MicroPython projects typically running on a micro controller.
    """

    def ignore_file(self, filename):
        """
        Returns true, if the given filename is a special file, that should
        neither be compiled nor deleted.
        """
        match os.path.normpath(filename):
            case "_build.py" | "boot.py" | "main.py":
                return True
            case _:
                return False

    def set_default_parameters(self):
        """
        Set default parameters from configuration.
        """
        self.parameters["march"] = self.config["app"]["march"]
    
    def do_dependencies(self):
        """
        Call `upip` to install dependencies.
        """
        pip_file = "requirements.txt"

        if not os.path.isfile(pip_file):
            return
        
        with open(pip_file) as pip_file:
            for line in pip_file.readlines():
                line = line.strip()
                comment_pos = line.find("#")
                line = line[:-comment_pos] if comment_pos > -1 else line

                if not line:
                    continue

                utils.micropython(self.config, self.build_dir, ["-m", "upip", "install", "-p", ".", line])

    def do_compile(self) -> None:
        """
        Call `mpy-cross` to compile all *.py source files to *.mpy binary files.
        """
        for dirpath, dirnames, filenames in os.walk("."):
            for filename in filenames:
                if not filename.lower().endswith(".py"):
                    continue

                filename = os.path.join(dirpath, filename)

                if not self.ignore_file(filename):
                    utils.mpy_cross(self.config, self.build_dir, [f"-march={self.parameters['march']}", filename])

    def do_finalize_build(self) -> None:
        """
        Delete the original *.py source files from the build directory.
        """
        for dirpath, dirnames, filenames in os.walk("."):
            for filename in filenames:
                if not filename.lower().endswith(".py"):
                    continue

                filename = os.path.join(dirpath, filename)

                if not self.ignore_file(filename):
                    utils.remove(filename)

class AppBuildCommand(Command, group="app", command="build"):
    """
    Compile and build the source code in the given directory
    $usage$ [march=armv7emsp] [<directory...>]

    This command takes the sources from one sub-project, copies them into the
    corresponding build directory and installs their dependencies as named in
    the file `requirements.txt`, if it exists. By default all sub-projects are
    built, unless the relative path of a specific source directory is given,
    in which case only that directory will be built.
    
    If a file called `_build.py` exists, it will be executed as an script directly
    after the sources have been copied into the build directory, with the build
    directory being set as the current working directory.

    After that, several build steps are executed, depending on the language
    runtime of the sub-project:

      * MicroPython:

          1. `upip` is used to install dependencies directly into the build directory.
          2. `mpy-cross` is used to convert all source *.py files into binary *.mpy files.
          3. The *.py source files are deleted, as they are not needed on the device.
    
      * Regular Python (e.g. CPython):

          1. A virtual environment is created in the sub-directory `env`.
          2. `pip` is used to install dependencies into the environment.

          There is no compilation step for regular Python, so that the *.py files are
          simply copied verbatim. The virtual environment is only created, if the file
          `requirements.txt` exists.
    
    In order for this command to know, which runtime shall be used, the sub-projects
    must be declared in the adjacent `make.conf` configuration file like this:

        [app]
        ./main            = micropython
        ./research/python = python
    
    The entries are recognized by the characters `./` at the beginning. Their key
    is the directory prefix and the value the runtime. Sub-directories automatically
    inherit the runtime setting from their parent.
    """

    def execute(self) -> None:
        for builder in SourceBuilder.create(self.config, self.arguments):
            builder.build()

class AppCleanCommand(Command, group="app", command="clean"):
    """
    Clean the compiled and built version of a source code
    $usage$ [<directory...>]

    This deletes the build directory matching the given source directories of
    one or more sub-projects. If no directory is given, all build directories
    that have a language runtime assigned in `make.conf` will be deleted.
    """

    def execute(self) -> None:
        for builder in SourceBuilder.create(self.config, self.arguments):
            builder.clean()
