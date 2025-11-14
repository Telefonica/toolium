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

from toolium.utils.ai_utils.accuracy import (get_accuracy_and_executions_from_tags, get_accuracy_data_suffix_from_tags,
                                             get_accuracy_data, store_execution_data)


accuracy_tags_examples = (
    (['accuracy'], {'accuracy': 0.9, 'executions': 10}),
    (['accuracy_85'], {'accuracy': 0.85, 'executions': 10}),
    (['accuracy_percent_80'], {'accuracy': 0.8, 'executions': 10}),
    (['accuracy_75_5'], {'accuracy': 0.75, 'executions': 5}),
    (['accuracy_percent_70_executions_3'], {'accuracy': 0.7, 'executions': 3}),
    (['other_tag', 'accuracy_95_15'], {'accuracy': 0.95, 'executions': 15}),
    (['no_accuracy_tag'], None),
    (['accuracy_85', 'accuracy_95_15'], {'accuracy': 0.85, 'executions': 10}),
    ([], None),
    (['accuracy_data', 'accuracy_data_50'], None),
    (['accuracy_75_5', 'accuracy_data'], {'accuracy': 0.75, 'executions': 5})
)


@pytest.mark.parametrize('tags, expected_accuracy_data', accuracy_tags_examples)
def test_get_accuracy_and_executions_from_tags(tags, expected_accuracy_data):
    accuracy_data = get_accuracy_and_executions_from_tags(tags)
    assert accuracy_data == expected_accuracy_data


accuracy_tags_examples = (
    (['accuracy'], 8, {'accuracy': 0.9, 'executions': 8}),
    (['accuracy_85'], 8, {'accuracy': 0.85, 'executions': 8}),
    (['accuracy_percent_80'], 8, {'accuracy': 0.8, 'executions': 8}),
    (['accuracy_75_5'], 8, {'accuracy': 0.75, 'executions': 5}),
    (['accuracy_percent_70_executions_3'], 8, {'accuracy': 0.7, 'executions': 3}),
    (['other_tag', 'accuracy_95_15'], 8, {'accuracy': 0.95, 'executions': 15}),
    (['no_accuracy_tag'], 8, None),
    (['accuracy_85', 'accuracy_95_15'], 8, {'accuracy': 0.85, 'executions': 8}),
    ([], 8, None),
    (['accuracy_data', 'accuracy_data_50'], 8, None),
    (['accuracy_75_5', 'accuracy_data'], 8, {'accuracy': 0.75, 'executions': 5})
)


@pytest.mark.parametrize('tags, data_length, expected_accuracy_data', accuracy_tags_examples)
def test_get_accuracy_and_executions_from_tags_with_data_length(tags, data_length, expected_accuracy_data):
    accuracy_data = get_accuracy_and_executions_from_tags(tags, accuracy_data_len=data_length)
    assert accuracy_data == expected_accuracy_data


accuracy_data_suffix_examples = (
    (['accuracy_data'], ''),
    (['accuracy_data_balance'], '_balance'),
    (['accuracy_data_balance_50'], '_balance_50'),
    (['other_tag', 'accuracy_data_transactions'], '_transactions'),
    (['no_accuracy_data_tag'], ''),
    (['accuracy', 'accuracy_85', 'accuracy_percent_70_executions_3'], ''),
    ([], '')
)


@pytest.mark.parametrize('tags, expected_data_suffix', accuracy_data_suffix_examples)
def test_get_accuracy_data_suffix_from_tags(tags, expected_data_suffix):
    data_suffix = get_accuracy_data_suffix_from_tags(tags)
    assert data_suffix == expected_data_suffix


@pytest.fixture
def context():
    context = mock.MagicMock()
    context.storage = {
        'accuracy_data': [{'question': 'Q1', 'answer': 'A1'},
                          {'question': 'Q2', 'answer': 'A2'}],
        'accuracy_data_balance': [{'question': 'Q1 balance', 'answer': 'A1'},
                                  {'question': 'Q2 balance', 'answer': 'A2'}],
        'accuracy_data_wrong': "This is not a list"
    }
    return context


def test_get_accuracy_data_default_suffix(context):
    data = get_accuracy_data(context, data_key_suffix='')
    assert data == [{'question': 'Q1', 'answer': 'A1'},
                    {'question': 'Q2', 'answer': 'A2'}]


def test_get_accuracy_data_with_suffix(context):
    data = get_accuracy_data(context, data_key_suffix='_balance')
    assert data == [{'question': 'Q1 balance', 'answer': 'A1'},
                    {'question': 'Q2 balance', 'answer': 'A2'}]


def test_get_accuracy_data_with_nonexistent_suffix(context):
    data = get_accuracy_data(context, data_key_suffix='_nonexistent')
    assert data == []


def test_get_accuracy_data_with_wrong_type(context):
    with pytest.raises(AssertionError) as exc:
        get_accuracy_data(context, data_key_suffix='_wrong')
    assert str(exc.value) == 'Expected accuracy_data_wrong must be a list: This is not a list'


def test_store_execution_data_default_suffix(context):
    store_execution_data(context, execution=0, data_key_suffix='')
    assert context.storage['accuracy_execution_data'] == {'question': 'Q1', 'answer': 'A1'}
    assert context.storage['accuracy_execution_index'] == 0
    store_execution_data(context, execution=1, data_key_suffix='')
    assert context.storage['accuracy_execution_data'] == {'question': 'Q2', 'answer': 'A2'}
    assert context.storage['accuracy_execution_index'] == 1
    store_execution_data(context, execution=2, data_key_suffix='')
    assert context.storage['accuracy_execution_data'] == {'question': 'Q1', 'answer': 'A1'}
    assert context.storage['accuracy_execution_index'] == 2


def test_store_execution_data_with_suffix(context):
    store_execution_data(context, execution=0, data_key_suffix='_balance')
    assert context.storage['accuracy_execution_data'] == {'question': 'Q1 balance', 'answer': 'A1'}
    assert context.storage['accuracy_execution_index'] == 0
    store_execution_data(context, execution=1, data_key_suffix='_balance')
    assert context.storage['accuracy_execution_data'] == {'question': 'Q2 balance', 'answer': 'A2'}
    assert context.storage['accuracy_execution_index'] == 1
    store_execution_data(context, execution=2, data_key_suffix='_balance')
    assert context.storage['accuracy_execution_data'] == {'question': 'Q1 balance', 'answer': 'A1'}
    assert context.storage['accuracy_execution_index'] == 2


def test_store_execution_data_with_nonexistent_suffix(context):
    store_execution_data(context, execution=0, data_key_suffix='_nonexistent')
    assert context.storage['accuracy_execution_data'] is None
    assert context.storage['accuracy_execution_index'] == 0
