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
from toolium.utils.ai_utils import (get_text_similarity_with_spacy, get_text_similarity_with_sentence_transformers,
                                    get_text_similarity_with_azure_openai, assert_text_similarity)


def configure_default_openai_model():
    """
    Configure OpenAI model used in unit tests
    """
    config = DriverWrappersPool.get_default_wrapper().config
    try:
        config.add_section('AI')
    except Exception:
        pass
    config.set('AI', 'openai_model', 'gpt-4o-mini')


get_similarity_examples = (
    ('Today it will be sunny', 'Today it will be sunny', 0.9, 1),
    ('Today is sunny', 'Today it will be sunny', 0.6, 0.9),
    ('It is sunny', 'Today it will be sunny', 0.5, 0.7),
    ('Nothing related', 'Today it will be sunny', 0, 0.6),
)


@pytest.mark.parametrize('input_text, expected_text, expected_low, expected_high', get_similarity_examples)
def test_get_text_similarity_with_spacy(input_text, expected_text, expected_low, expected_high):
    similarity = get_text_similarity_with_spacy(input_text, expected_text)
    assert expected_low <= similarity <= expected_high


@pytest.mark.parametrize('input_text, expected_text, expected_low, expected_high', get_similarity_examples)
def test_get_text_similarity_with_sentence_transformers(input_text, expected_text, expected_low, expected_high):
    similarity = get_text_similarity_with_sentence_transformers(input_text, expected_text)
    assert expected_low <= similarity <= expected_high


get_openai_similarity_examples = (
    ('Today it will be sunny', 'Today it will be sunny', 0.9, 1),
    ('Today is sunny', 'Today it will be sunny', 0.7, 0.9),
    ('It is sunny', 'Today it will be sunny', 0.7, 0.9),
    ('Nothing related', 'Today it will be sunny', 0, 0.1),
    ('Today it will be cloudy', 'Today it will be sunny', 0, 0.1),
    ('A splendid and rainless day is expected', 'Today it will be sunny', 0.8, 1),
)


@pytest.mark.parametrize('input_text, expected_text, expected_low, expected_high', get_openai_similarity_examples)
def test_get_text_similarity_with_azure_openai(input_text, expected_text, expected_low, expected_high):
    configure_default_openai_model()
    similarity = get_text_similarity_with_azure_openai(input_text, expected_text)
    assert expected_low <= similarity <= expected_high


assert_similarity_passed_examples = (
    ('Today it will be sunny', 'Today it will be sunny', 0.9),
    ('Today it will be sunny', ['Nothing related', 'Today it will be sunny'], 0.9),
    ('Today is sunny', ['It will be nice', 'Today it will be sunny'], 0.6),
)


@pytest.mark.parametrize('input_text, expected_text, threshold', assert_similarity_passed_examples)
def test_assert_text_similarity_with_spacy_passed(input_text, expected_text, threshold):
    assert_text_similarity(input_text, expected_text, threshold=threshold, similarity_method='spacy')


@pytest.mark.parametrize('input_text, expected_text, threshold', assert_similarity_passed_examples)
def test_assert_text_similarity_with_sentence_transformers_passed(input_text, expected_text, threshold):
    assert_text_similarity(input_text, expected_text, threshold=threshold, similarity_method='sentence_transformers')


@pytest.mark.parametrize('input_text, expected_text, threshold', assert_similarity_passed_examples)
def test_assert_text_similarity_with_openai_passed(input_text, expected_text, threshold):
    configure_default_openai_model()
    assert_text_similarity(input_text, expected_text, threshold=threshold, similarity_method='azure_openai')


assert_similarity_failed_examples = (
    ('Today it will be sunny', 'Nothing related', 0.9),
    ('Today it will be sunny', ['Nothing related', 'It is sunny'], 0.9),
)


@pytest.mark.parametrize('input_text, expected_text, threshold', assert_similarity_failed_examples)
def test_assert_text_similarity_with_spacy_failed(input_text, expected_text, threshold):
    with pytest.raises(Exception) as excinfo:
        assert_text_similarity(input_text, expected_text, threshold=threshold, similarity_method='spacy')
    assert str(excinfo.value).startswith('Similarity between received and expected texts is below threshold')


@pytest.mark.parametrize('input_text, expected_text, threshold', assert_similarity_failed_examples)
def test_assert_text_similarity_with_sentence_transformers_failed(input_text, expected_text, threshold):
    with pytest.raises(Exception) as excinfo:
        assert_text_similarity(input_text, expected_text, threshold=threshold, similarity_method='sentence_transformers')
    assert str(excinfo.value).startswith('Similarity between received and expected texts is below threshold')


assert_openai_similarity_failed_examples = (
    ('Today it will be sunny', 'Nothing related', 0.9),
    ('Today it will be sunny', ['Nothing related', 'Today it is cold'], 0.9),
)


@pytest.mark.parametrize('input_text, expected_text, threshold', assert_openai_similarity_failed_examples)
def test_assert_text_similarity_with_openai_failed(input_text, expected_text, threshold):
    configure_default_openai_model()
    with pytest.raises(Exception) as excinfo:
        assert_text_similarity(input_text, expected_text, threshold=threshold, similarity_method='azure_openai')
    assert str(excinfo.value).startswith('Similarity between received and expected texts is below threshold')


@mock.patch('toolium.utils.ai_utils.get_text_similarity_with_spacy')
def test_assert_text_similarity_with_default_method(similarity_mock):
    similarity_mock.return_value = 0.9
    input_text = 'Today it will be sunny'
    expected_text = 'Today is sunny'
    assert_text_similarity(input_text, expected_text, threshold=0.8)
    similarity_mock.assert_called_once_with(input_text, expected_text)


@mock.patch('toolium.utils.ai_utils.get_text_similarity_with_sentence_transformers')
def test_assert_text_similarity_with_configured_method(similarity_mock):
    config = DriverWrappersPool.get_default_wrapper().config
    try:
        config.add_section('AI')
    except Exception:
        pass
    config.set('AI', 'text_similarity_method', 'sentence_transformers')
    similarity_mock.return_value = 0.9

    input_text = 'Today it will be sunny'
    expected_text = 'Today is sunny'
    assert_text_similarity(input_text, expected_text, threshold=0.8)
    similarity_mock.assert_called_once_with(input_text, expected_text)


@mock.patch('toolium.utils.ai_utils.get_text_similarity_with_spacy')
def test_assert_text_similarity_with_configured_and_explicit_method(similarity_mock):
    config = DriverWrappersPool.get_default_wrapper().config
    try:
        config.add_section('AI')
    except Exception:
        pass
    config.set('AI', 'text_similarity_method', 'sentence_transformers')
    similarity_mock.return_value = 0.9

    input_text = 'Today it will be sunny'
    expected_text = 'Today is sunny'
    assert_text_similarity(input_text, expected_text, threshold=0.8, similarity_method='spacy')
    similarity_mock.assert_called_once_with(input_text, expected_text)
