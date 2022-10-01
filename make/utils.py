# µKlavier - Digital audio synthesizer made with Micropython
# Copyright © 2022  Dennis Schulmeister-Zimolong <dennis@zimolong.eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

"""
Utilities with shared code for the commands.
"""

import os, platform, shutil, subprocess
from configparser import ConfigParser
from typing import List

from .base import CommandError

def print_box(message: str):
    """
    Print a blue colored title box on the console.
    """
    # See: https://en.wikipedia.org/wiki/ANSI_escape_code#3-bit_and_4-bit
    color_on  = "\033[93;44m\033[1m"
    color_off = "\033[0m"
    line      = "═" * len(message)
    bar       = "║"
    tl        = "╔"
    tr        = "╗"
    bl        = "╚"
    br        = "╝"

    print(f"{color_on}{tl}{line}{tr}{color_off}")
    print(f"{color_on}{bar}{message}{bar}{color_off}")
    print(f"{color_on}{bl}{line}{br}{color_off}")
    print("")

def print_step(message: str):
    """
    Print a bold yellow description of the next step.
    """
    color_on  = "\033[33m\033[1m"
    color_off = "\033[0m"
    print(f"» {color_on}{message}{color_off}")

def print_error(message: str):
    """
    Print a bold red error message.
    """
    color_on  = "\033[31m\033[1m"
    color_off = "\033[0m"
    print(f"{color_on}{message}{color_off}")

def print_line(message: str):
    """
    Print some other output.
    """
    print(message)

def run(args: List[str], shell: bool = False, **kwargs) -> None:
    """
    Tiny wrapper around `subprocess.run` for calling external programs. This
    automatically raises the built-in `CalledProcessError` exception for any
    non-zero return code to terminate the build process.
    """
    print_step(" ".join(args))
    subprocess.run(args, shell=shell, **kwargs).check_returncode()

def chdir(path: str, **kwargs) -> None:
    """
    Tiny wrapper around `os.chdir` that prints a description of what it is doing, first.
    """
    print_step(f"Change to directory {path}")
    os.chdir(path, **kwargs)

def makedirs(path: str, **kwargs) -> None:
    """
    Recursively create a directory hierarchy. Tiny wrapper around `os.makedirs`
    that prints a description of what it is doing, first.
    """
    print_step(f"Create directory {path}")
    os.makedirs(path, **kwargs)

def rmtree(path: str, **kwargs) -> None:
    """
    Recursively delete directory hierarchy. Tiny wrapper around `shutil.rmtree`
    that prints a description of what it is doing, first.
    """
    print_step(f"Delete directory {path}")

    try:
        shutil.rmtree(path, ignore_errors=True, **kwargs)
    except FileNotFoundError:
        pass

def copytree(src, dst, **kwargs) -> None:
    """
    Recursively copy the content of one directory into another directory.
    The destination directory will be automatically created, if it does not
    exist. This is more or less a tiny wrapper around `shutil.copytree` that
    prints a descriptions of what it is doing, first.
    """
    print_step(f"Copy contents of directory {src} to {dst}")
    shutil.copytree(src, dst, dirs_exist_ok=True, **kwargs)

def remove(path, **kwargs) -> None:
    """
    Delete a single file. Tiny wrapper around `os.remove` that prints a
    description of what it is doing, first
    """
    print_step(f"Delete {path}")
    os.remove(path, **kwargs)

def git_clone(git_url: str, target_dir: str, commit: str = "", branch: str = "", depth: int = 1) -> None:
    """
    Clone the given git repository into the given directory. Optionally a specific
    tag or commit id can be specified. By default only the latest version is cloned
    to save bandwidth and time, as the history is usually not needed here.

    Parameters:

     * `git_url`: Git repository to clone
     * `target_dir`: Target directory
     * `commit`: Commit reference, branch name or tag name (optional)
     * `depth': Clone depth (default: 1)

    As per the git documentation, branches and tags are just references to specific
    commits and can thus be used as an alternative to the commit hash during checkout.
    The difference between branches and tags is, that branches can have their own follow-up
    commits, creating an alternate history of the repository, while tags can't. Usually,
    all this shouldn't be a problem here, as we are only pulling external source code
    to use it during the build. But if local changes should be made to the code, it will
    be necessary to manually create branch, first.
    """
    old_cwd = os.getcwd()
    chdir(target_dir)

    run(["git", "clone", f"--depth={depth}", git_url, "."])
    run(["git", "fetch"])
    run(["git", "fetch", "--tags"])

    if commit:
        cmd = ["git", "checkout", commit]

        run(cmd)

        print("")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("~ NOTE: You are not following the master branch. Make sure to   ~")
        print("~ to create a new branch before making any commits. If this is  ~")
        print("~ is a remote branch, you will otherwise not be able to push.   ~")
        print("~ If this is a tag, new commits will otherwise be unreachable!  ~")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    
    chdir(old_cwd)

def get_micropython_dir(config: ConfigParser, basedir: str) -> str:
    """
    Get the base directory of the local MicroPython installation (as built with
    the commands from the micropython group).
    """
    result = config["micropython"]["target_dir"] + "/ports/"
    result += "windows" if platform.system() == "Windows" else "unix"
    result = result.replace("/", os.path.sep)
    result = os.path.relpath(result, start=basedir)
    return result

def get_mpy_cross_dir(config: ConfigParser, basedir: str) -> str:
    """
    Get the base directory of the local mpy-cross installation (as built with
    the commands from the micropython group).
    """
    result = config["micropython"]["target_dir"] + "/mpy-cross"
    result = result.replace("/", os.path.sep)
    result = os.path.relpath(result, start=basedir)
    return result

def micropython(config: ConfigParser, basedir: str, args: List[str]):
    """
    Run the locally built MicroPython interpreter with the given command line arguments.
    """
    cmd = [os.path.join(get_micropython_dir(config, basedir), "micropython")]
    cmd.extend(args)
    run(cmd)

def mpy_cross(config: ConfigParser, basedir: str, args: List[str]):
    """
    Run the locally build mpy-cross with the given command line arguments.
    """
    cmd = [os.path.join(get_mpy_cross_dir(config, basedir), "mpy-cross")]
    cmd.extend(args)
    run(cmd)
