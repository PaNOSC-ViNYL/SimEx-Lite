# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Utils io module"""

from typing import List, Optional
from collections.abc import Iterable
import re


def is_list_like(variable):
    return isinstance(variable, Iterable) and not isinstance(variable, (str, bytes))


class UnknownFileTypeError(Exception):
    pass


def parseIndex(index):
    """Parse the index parameter"""
    if isinstance(index, str):
        index = string2index(index)
    elif isinstance(index, slice):
        return index
    elif index is None:
        index = slice(None, None, None)
    elif is_list_like(index):
        return index
    elif isinstance(index, int):
        index = slice(index, (index + 1))
    else:
        raise ValueError(f"Cannot parse input index: {index}")

    # if index is None or index == ':':
    # index = slice(None, None, None)
    # if not isinstance(index, (slice, str)):
    #     index = slice(index, (index + 1))
    return index


def string2index(string: str):
    """Convert index string to either int or slice"""
    if ":" not in string:
        return int(string)
    i: List[Optional[int]] = []
    for s in string.split(":"):
        if s == "":
            i.append(None)
        else:
            i.append(int(s))
    i += (3 - len(i)) * [None]
    return slice(*i)


def replace_after_substring_in_file(
    file_path, substring, replacement, output_file_path=None
):
    # Read the content of the file
    with open(file_path, "r") as file:
        content = file.read()

    # Define the pattern to match the substring followed by anything until the end of the line
    pattern = re.compile(f"({substring}.*$)", re.MULTILINE)
    # Replace the matched pattern with the replacement
    new_content = pattern.sub(replacement, content)

    # Write the new content back to the file or to a new file
    if output_file_path:
        with open(output_file_path, "w") as file:
            file.write(new_content)
    else:
        with open(file_path, "w") as file:
            file.write(new_content)
