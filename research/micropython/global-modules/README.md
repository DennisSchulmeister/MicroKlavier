Global modules in special lib-directory
=======================================

This experiment tries to put a module in the special `lib` directory
so that it can be imported from any module like a built-in module from
MicroPython.

By placing a `*.py`-file in the `lib` directory (e.g. `my_module.py`)
it can be simple imported as `import my_module` from anywhere in the
source code.

This will be useful to provide a dummy implementation of CPythons
`typing` module that is so far missing in MicroPython despite a
never accepted pull request from 2018.

See: https://github.com/micropython/micropython-lib/pull/297