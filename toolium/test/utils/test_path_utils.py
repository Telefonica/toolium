# -*- coding: utf-8 -*-
"""
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

import os
import pytest
import queue as queue
import threading
import uuid

from toolium.utils.path_utils import get_valid_filename, makedirs_safe

filename_tests = (
    ('hola_pepito', 'hola_pepito'),
    (' hola:pep /ito* ', 'hola_pep__ito'),
    ('successful login -- @1.1 john.doe', 'successful_login_1_1_john_doe'),
    ('successful login -- @1.2 Mark options: {Length=10 Mark=mark File=file_name.jpg}',
     'successful_login_1_2_Mark_options___Length_10_Mark_mark_File_file_name_jpg'),
    ('successful login -- @1.3 acción', 'successful_login_1_3_accion'),
)


@pytest.mark.parametrize('input_filename, expected_filename', filename_tests)
def test_get_valid_filename(input_filename, expected_filename):
    valid_filename = get_valid_filename(input_filename)

    assert expected_filename == valid_filename


def test_get_valid_filename_length():
    input_filename = ' hola:pep /ito* '
    expected_filename = 'hola_pep__it'
    valid_filename = get_valid_filename(input_filename, 12)

    assert expected_filename == valid_filename


def test_create_new_folder():
    folder = os.path.join('output', str(uuid.uuid4()))
    makedirs_safe(folder)

    assert os.path.isdir(folder)
    os.rmdir(folder)


def test_create_existing_folder():
    folder = os.path.join('output', str(uuid.uuid4()))
    os.makedirs(folder)
    makedirs_safe(folder)

    assert os.path.isdir(folder)
    os.rmdir(folder)


def test_create_new_folder_parallel():
    folder = os.path.join('output', str(uuid.uuid4()))

    def run_makedirs(folder, exceptions):
        try:
            makedirs_safe(folder)
        except Exception as exc:
            exceptions.put(exc)

    for _ in range(5):
        exceptions = queue.Queue()
        thread1 = threading.Thread(target=run_makedirs, args=(folder, exceptions))
        thread2 = threading.Thread(target=run_makedirs, args=(folder, exceptions))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        assert exceptions.qsize() == 0
        assert os.path.isdir(folder)
        os.rmdir(folder)


def test_path_utils_filename_compatibility():
    # Check that path_utils works with old imports
    from toolium.utils.path_utils import get_valid_filename

    assert 'test' == get_valid_filename('test')


def test_path_utils_makedirs_compatibility():
    # Check that path_utils works with old imports
    from toolium.utils.path_utils import makedirs_safe

    folder = os.path.join('output', str(uuid.uuid4()))
    makedirs_safe(folder)
    assert os.path.isdir(folder)
    os.rmdir(folder)
