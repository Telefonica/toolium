# -*- coding: utf-8 -*-

# Copyright (c) Telefónica Digital.
# QA Team <qacdco@telefonica.com>


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
