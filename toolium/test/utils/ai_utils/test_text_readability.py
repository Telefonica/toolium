# -*- coding: utf-8 -*-
"""
Copyright 2025 Telefónica Innovación Digital, S.L.
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
import pytest

from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.utils.ai_utils.text_readability import get_text_readability_with_spacy, assert_text_readability


get_readability_examples = (
    ('This is a human readable text', 0.9, 1),
    ('Short message', 0.9, 1),
    ('Error in a backend system', 0.9, 1),
    ('Insufficient', 0.0, 0.1),
    ('sdfajla afadfaj', 0.0, 0.1),
    ('Too many symbols: [ separators | hyphens - and such ] = {}', 0.0, 0.5),
    ('CODE-323424', 0, 0.5),
    ('Error SVC-2342', 0.0, 0.5),
    ('Error in impl/modules/auth_code/user_check.py', 0.0, 0.5),
    ('KeyError in user_check.py:38', 0.0, 0.5),
)


@pytest.mark.parametrize('input_text, expected_low, expected_high', get_readability_examples)
def test_get_text_readability_with_spacy(input_text, expected_low, expected_high):
    readability = get_text_readability_with_spacy(input_text)
    assert expected_low <= readability <= expected_high


assert_readability_passed_examples = (
    ('This is a human readable text', 0.9),
    ('Short message', 0.9),
    ('Error in a backend system', 0.9),
)


@pytest.mark.parametrize('input_text, threshold', assert_readability_passed_examples)
def test_assert_text_readability_with_spacy_passed(input_text, threshold):
    assert_text_readability(input_text, threshold=threshold, readability_method='spacy')


assert_readability_failed_examples = (
    ('Insufficient', 0.1),
    ('sdfajla afadfaj', 0.1),
    ('CODE-323424', 0.5),
)


@pytest.mark.parametrize('input_text, threshold', assert_readability_failed_examples)
def test_assert_text_readability_with_spacy_failed(input_text, threshold):
    with pytest.raises(Exception) as excinfo:
        assert_text_readability(input_text, threshold=threshold, readability_method='spacy')
    assert str(excinfo.value).startswith('Text readability is below threshold')


def test_assert_text_readability_with_custom_technical_chars():
    input_text = 'Too many symbols: [ separators | hyphens - and such ] = {}'
    with pytest.raises(Exception) as excinfo:
        assert_text_readability(input_text, threshold=0.9)
    assert str(excinfo.value).startswith('Text readability is below threshold')
    assert_text_readability(input_text, threshold=0.9, technical_chars=['_'])  # ignoring other technical chars


@mock.patch('toolium.utils.ai_utils.text_readability.get_text_readability_with_spacy')
def test_assert_text_readability_with_default_method(readability_mock):
    readability_mock.return_value = 0.9
    input_text = 'This is a human readable text'
    assert_text_readability(input_text, threshold=0.8)
    readability_mock.assert_called_once_with(input_text, None, None)


@mock.patch('toolium.utils.ai_utils.text_readability.get_text_readability_with_spacy')
def test_assert_text_readability_with_configured_and_explicit_method(readability_mock):
    config = DriverWrappersPool.get_default_wrapper().config
    try:
        config.add_section('AI')
    except Exception:
        pass
    config.set('AI', 'text_readability_method', 'sentence_transformers')
    readability_mock.return_value = 0.9

    input_text = 'This is a human readable text'
    assert_text_readability(input_text, threshold=0.8, readability_method='spacy')
    readability_mock.assert_called_once_with(input_text, None, None)


@mock.patch('toolium.utils.ai_utils.text_readability.get_text_readability_with_spacy')
def test_assert_text_readability_with_configured_and_explicit_model(readability_mock):
    config = DriverWrappersPool.get_default_wrapper().config
    try:
        config.add_section('AI')
    except Exception:
        pass
    config.set('AI', 'text_readability_method', 'spacy')
    readability_mock.return_value = 0.9

    input_text = 'This is a human readable text'
    assert_text_readability(input_text, threshold=0.8, model_name='en_core_web_lg')
    readability_mock.assert_called_once_with(input_text, None, 'en_core_web_lg')


@mock.patch('toolium.utils.ai_utils.text_readability.get_text_readability_with_spacy')
def test_assert_text_readability_with_configured_and_explicit_method_and_model(readability_mock):
    config = DriverWrappersPool.get_default_wrapper().config
    try:
        config.add_section('AI')
    except Exception:
        pass
    config.set('AI', 'text_readability_method', 'sentence_transformers')
    readability_mock.return_value = 0.9

    input_text = 'This is a human readable text'
    assert_text_readability(input_text, threshold=0.8, readability_method='spacy',
                            model_name='en_core_web_lg')
    readability_mock.assert_called_once_with(input_text, None, 'en_core_web_lg')
