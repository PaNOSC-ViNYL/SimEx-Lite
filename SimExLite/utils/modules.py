"""Python wrapper around environment modules ("module load")
by Thomas Kluyver
"""
import os
import shlex
from subprocess import run, PIPE


def _modulecmd(*args):
    cmd = ["modulecmd", "python"] + list(args)
    res = run(cmd, stdout=PIPE, stderr=PIPE)
    txt = res.stderr.decode("utf-8", "replace").strip()
    if txt:
        print(txt)

    res.check_returncode()

    code = res.stdout.decode("utf-8").strip()
    if code:
        exec(code, {"os": os})


def _cmd(*args):
    cmd = list(args)
    res = run(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    txt = res.stderr.decode("utf-8", "replace").strip()
    if txt:
        print(txt)

    res.check_returncode()

    code = res.stdout.decode("utf-8").strip()
    if code:
        # exec(code, {"os": os})
        print(code)


def load(*args):
    _modulecmd("load", *args)


def unload(*args):
    _modulecmd("unload", *args)
