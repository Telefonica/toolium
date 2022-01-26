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

from toolium.utils.poeditor import get_valid_lang


def test_poe_lang_param():
    """
    Verification of a POEditor language param
    """
    context = mock.MagicMock()
    context.poeditor_language_list = ['en-gb', 'de', 'pt-br', 'es', 'es-ar', 'es-cl', 'es-co', 'es-ec']
    assert get_valid_lang(context, 'pt-br') == 'pt-br'
    assert get_valid_lang(context, 'es') == 'es'
    assert get_valid_lang(context, 'es-es') == 'es'
    assert get_valid_lang(context, 'es-co') == 'es-co'
