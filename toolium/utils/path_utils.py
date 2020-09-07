# -*- coding: utf-8 -*-
u"""
Copyright 2018 Telefónica Investigación y Desarrollo, S.A.U.
This file is part of Toolium.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from os import makedirs
try:
    from os import errno  # Py2, < Py3.7
except ImportError:
    import errno  # Py3.7
import re

FILENAME_MAX_LENGTH = 100


def get_valid_filename(s, max_length=FILENAME_MAX_LENGTH):
    """
    Returns the given string converted to a string that can be used for a clean filename.
    Removes leading and trailing spaces; converts anything that is not an alphanumeric,
    dash or underscore to underscore; converts behave examples separator ` -- @` to underscore.
    It also cuts the resulting name to `max_length`.

    @see https://github.com/django/django/blob/master/django/utils/text.py
    """
    s = str(s).strip().replace(' -- @', '_')
    s = re.sub(r'(?u)[^-\w]', '_', s).strip('_')
    return s[:max_length]


def makedirs_safe(folder):
    """
    Create a new folder if it does not exist
    :param folder: folder path
    """
    try:
        makedirs(folder)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
