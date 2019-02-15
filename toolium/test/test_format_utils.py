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

import pytest
import toolium.format_utils as format_utils

filename_tests = (
    ('hola_pepito', 'hola_pepito'),
    (' hola:pep /ito* ', 'hola_pep__ito'),
    ('successful login -- @1.1 john.doe', 'successful_login_1_1_john_doe'),
    ('successful login -- @1.2 Mark options: {Length=10 Mark=mark File=file_name.jpg}',
     'successful_login_1_2_Mark_options___Length_10_Mark_mark_File_file_name_jpg'),
)


@pytest.mark.parametrize('input_filename, expected_filename', filename_tests)
def test_get_valid_filename(input_filename, expected_filename):
    valid_filename = format_utils.get_valid_filename(input_filename)

    assert expected_filename == valid_filename


def test_get_valid_filename_length():
    input_filename = ' hola:pep /ito* '
    expected_filename = 'hola_pep__it'
    valid_filename = format_utils.get_valid_filename(input_filename, 12)

    assert expected_filename == valid_filename
