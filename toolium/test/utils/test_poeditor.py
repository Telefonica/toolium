# -*- coding: utf-8 -*-
"""
Copyright 2022 Telefónica Investigación y Desarrollo, S.A.U.
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

import mock
import os
import pytest

from toolium.config_parser import ExtendedConfigParser
from toolium.utils import dataset, poeditor
from toolium.utils.poeditor import get_valid_lang, load_poeditor_texts


def test_get_valid_lang():
    """
    Verification of a POEditor language param
    """
    language_codes = ['en-gb', 'de', 'pt-br', 'es', 'es-ar', 'es-cl', 'es-co', 'es-ec']
    assert get_valid_lang(language_codes, 'pt-br') == 'pt-br'
    assert get_valid_lang(language_codes, 'es') == 'es'
    assert get_valid_lang(language_codes, 'es-es') == 'es'
    assert get_valid_lang(language_codes, 'es-co') == 'es-co'


def test_get_valid_lang_wrong_lang():
    """
    Verification of a POEditor language param
    """
    language_codes = ['en-gb', 'de', 'pt-br']
    with pytest.raises(Exception) as excinfo:
        get_valid_lang(language_codes, 'en-en')
    assert "Language en-en is not included in valid codes: en-gb, de, pt-br" == str(excinfo.value)


def test_poe_lang_param_from_project_config():
    """
    Verification of a POEditor language param getting language from project config
    """
    config_file_path = os.path.join("toolium", "test", "resources", "toolium.cfg")
    dataset.toolium_config = ExtendedConfigParser.get_config_from_file(config_file_path)
    language_codes = ['en-gb', 'de', 'pt-br', 'es', 'es-ar', 'es-cl', 'es-co', 'es-ec', 'en']
    assert get_valid_lang(language_codes) == 'en'


def test_load_poeditor_texts_without_api_token():
    """
    Verification of POEditor texts load abortion when api_token is not configured
    """
    dataset.project_config = {
        "poeditor": {
            "project_name": "My-Bot"
        }
    }
    poeditor.logger = mock.MagicMock()

    load_poeditor_texts()
    poeditor.logger.info.assert_called_with("POEditor is not configured")
