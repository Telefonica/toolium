# -*- coding: utf-8 -*-
"""
Copyright 2023 Telefónica Investigación y Desarrollo, S.A.U.
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

from toolium.utils import dataset
from toolium.utils.data_generator import DataGenerator


def test_get_locale():
    dataset.language = 'pt'
    dataset.country = 'BR'
    expected_locale = 'pt_BR'
    locale = DataGenerator.get_locale()
    assert expected_locale == locale


def test_get_locale_lowcase():
    dataset.language = 'pt'
    dataset.country = 'br'
    expected_locale = 'pt_BR'
    locale = DataGenerator.get_locale()
    assert expected_locale == locale


def test_get_locale_only_from_language():
    dataset.language = 'pt-br'
    dataset.country = None
    expected_locale = 'pt_BR'
    locale = DataGenerator.get_locale()
    assert expected_locale == locale


def test_get_locale_no_language_and_country():
    dataset.language = None
    dataset.country = None
    expected_locale = 'es_ES'
    locale = DataGenerator.get_locale()
    assert expected_locale == locale


def test_get_locale_no_country():
    dataset.language = 'pt'
    dataset.country = None
    expected_locale = 'es_ES'
    locale = DataGenerator.get_locale()
    assert expected_locale == locale
