# Copyright (C)  Juncheng E 
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Console script for SimExLite."""
import argparse
import sys


def main():
    """Console script for SimExLite."""
    parser = argparse.ArgumentParser()
    parser.add_argument('_', nargs='*')
    args = parser.parse_args()

    print("Arguments: " + str(args._))
    print("Replace this message by putting your code into "
          "SimExLite.cli.main")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
