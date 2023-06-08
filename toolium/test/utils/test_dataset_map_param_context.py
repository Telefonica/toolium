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

import pytest

from toolium.utils import dataset
from toolium.utils.dataset import map_param


def test_a_context_param():
    """
    Verification of a mapped parameter as CONTEXT
    """
    class Context(object):
        pass
    context = Context()
    context.attribute = "attribute value"
    context.storage = {"storage_key": "storage entry value"}
    context.feature_storage = {"feature_storage_key": "feature storage entry value"}
    dataset.behave_context = context

    result_att = map_param("[CONTEXT:attribute]")
    expected_att = "attribute value"
    assert expected_att == result_att


def test_a_context_param_storage():
    """
    Verification of a mapped parameter as CONTEXT saved in storage
    """
    class Context(object):
        pass
    context = Context()
    context.attribute = "attribute value"
    context.storage = {"storage_key": "storage entry value"}
    context.feature_storage = {"feature_storage_key": "feature storage entry value"}
    dataset.behave_context = context

    result_st = map_param("[CONTEXT:storage_key]")
    expected_st = "storage entry value"
    assert expected_st == result_st


def test_a_context_param_feature_storage():
    """
    Verification of a mapped parameter as CONTEXT saved in feature storage
    """
    class Context(object):
        pass
    context = Context()
    context.attribute = "attribute value"
    context.storage = {"storage_key": "storage entry value"}
    context.feature_storage = {"feature_storage_key": "feature storage entry value"}
    dataset.behave_context = context

    result_st = map_param("[CONTEXT:feature_storage_key]")
    expected_st = "feature storage entry value"
    assert expected_st == result_st


def test_a_context_param_storage_and_feature_storage():
    """
    Verification of a mapped parameter as CONTEXT saved in storage and feature storage
    """
    class Context(object):
        pass
    context = Context()
    context.attribute = "attribute value"
    context.storage = {"storage_key": "storage entry value"}
    context.feature_storage = {"storage_key": "feature storage entry value"}
    dataset.behave_context = context

    result_st = map_param("[CONTEXT:storage_key]")
    expected_st = "storage entry value"
    assert expected_st == result_st


def test_a_context_param_without_storage_and_feature_storage():
    """
    Verification of a mapped parameter as CONTEXT when before_feature and before_scenario have not been executed, so
    storage and feature_storage are not initialized
    """
    class Context(object):
        pass
    context = Context()
    context.attribute = "attribute value"
    dataset.behave_context = context

    result_att = map_param("[CONTEXT:attribute]")
    expected_att = "attribute value"
    assert expected_att == result_att


def test_a_context_param_storage_without_feature_storage():
    """
    Verification of a mapped parameter as CONTEXT saved in storage when before_feature has been executed, so
    feature_storage is not initialized
    """
    class Context(object):
        pass
    context = Context()
    context.attribute = "attribute value"
    context.storage = {"storage_key": "storage entry value"}
    dataset.behave_context = context

    result_st = map_param("[CONTEXT:storage_key]")
    expected_st = "storage entry value"
    assert expected_st == result_st


def test_a_context_param_dict():
    """
    Verification of a mapped parameter in a dict as CONTEXT
    """
    class Context(object):
        pass
    context = Context()

    context.one = {"two": {"three": "the value"}}
    dataset.behave_context = context

    result_att = map_param("[CONTEXT:one.two.three]")
    expected_att = "the value"
    assert expected_att == result_att


def test_a_context_param_class():
    """
    Verification of a mapped parameter in a class as CONTEXT
    """
    class Context(object):
        pass
    context = Context()

    class OneClass(object):
        pass
    one = OneClass()

    class TwoClass(object):
        pass
    two = TwoClass()
    two.three = "the value"
    one.two = two
    context.one = one
    dataset.behave_context = context

    result_att = map_param("[CONTEXT:one.two.three]")
    expected_att = "the value"
    assert expected_att == result_att


def test_a_context_param_dict_class():
    """
    Verification of a mapped parameter in a dict inside a class as CONTEXT
    """
    class Context(object):
        pass
    context = Context()

    class TwoClass(object):
        pass
    two = TwoClass()
    two.three = "the value"
    context.one = {"two": two}
    dataset.behave_context = context

    result_att = map_param("[CONTEXT:one.two.three]")
    expected_att = "the value"
    assert expected_att == result_att


def test_a_context_param_storage_class():
    """
    Verification of a mapped parameter in a class as CONTEXT saved in storage
    """
    class Context(object):
        pass
    context = Context()

    class OneClass(object):
        pass
    one = OneClass()

    class TwoClass(object):
        pass
    two = TwoClass()
    two.three = "the value"
    one.two = two
    context.storage = {"one": one}
    context.feature_storage = {}
    dataset.behave_context = context

    result_att = map_param("[CONTEXT:one.two.three]")
    expected_att = "the value"
    assert expected_att == result_att


def test_a_context_param_without_storage():
    """
    Verification of a mapped parameter as CONTEXT when storage is not initialized
    """
    class Context(object):
        pass
    context = Context()
    context.attribute = "attribute value"
    dataset.behave_context = context

    result_att = map_param("[CONTEXT:attribute]")
    expected_att = "attribute value"
    assert expected_att == result_att


def test_a_context_param_unknown():
    """
    Verification of an unknown mapped parameter as CONTEXT
    """
    class Context(object):
        pass
    context = Context()
    context.attribute = "attribute value"
    context.storage = {"storage_key": "storage entry value"}
    context.feature_storage = {}
    dataset.behave_context = context

    with pytest.raises(Exception) as excinfo:
        map_param("[CONTEXT:unknown]")
    assert "'unknown' key not found in context" == str(excinfo.value)


def test_a_context_param_class_unknown():
    """
    Verification of an unknown mapped parameter in a class as CONTEXT
    """
    class Context(object):
        pass
    context = Context()
    context.storage = {}
    context.feature_storage = {}

    class OneClass(object):
        pass
    context.one = OneClass()
    context.one.two = "the value"
    dataset.behave_context = context

    with pytest.raises(Exception) as excinfo:
        map_param("[CONTEXT:one.three]")
    assert "'three' attribute not found in OneClass class in context" == str(excinfo.value)


def test_a_context_param_dict_unknown():
    """
    Verification of an unknown mapped parameter in a dict as CONTEXT
    """
    class Context(object):
        pass
    context = Context()

    context.one = {"two": {"three": "the value"}}
    dataset.behave_context = context

    with pytest.raises(Exception) as excinfo:
        map_param("[CONTEXT:one.three]")
    assert f"'three' key not found in {context.one} value in context" == str(excinfo.value)


def test_a_context_param_list():
    """
    Verification of a list without index as CONTEXT to get all the list, not a element in the list
    """
    class Context(object):
        pass
    context = Context()

    context.list = {
        'cmsScrollableActions': [
            {
                'id': 'ask-for-duplicate',
                'text': 'QA duplica'
            },
            {
                'id': 'ask-for-qa',
                'text': 'QA no duplica'
            }
        ]
    }
    dataset.behave_context = context

    assert map_param("[CONTEXT:list.cmsScrollableActions]") == [{'id': 'ask-for-duplicate', 'text': 'QA duplica'},
                                                                {'id': 'ask-for-qa', 'text': 'QA no duplica'}]


def test_a_context_param_list_default():
    """
    Verification of a list without index as CONTEXT (get the attribute of the first element in list)
    """
    class Context(object):
        pass
    context = Context()

    context.list = {
        'cmsScrollableActions': [
            {
                'id': 'ask-for-duplicate',
                'text': 'QA duplica'
            },
            {
                'id': 'ask-for-qa',
                'text': 'QA no duplica'
            }
        ]
    }
    dataset.behave_context = context
    assert map_param("[CONTEXT:list.cmsScrollableActions.text]") == 'QA duplica'


def test_a_context_param_list_correct_index():
    """
    Verification of a list with a correct index (In bounds) as CONTEXT
    """
    class Context(object):
        pass
    context = Context()

    context.list = {
        'cmsScrollableActions': [
            {
                'id': 'ask-for-duplicate',
                'text': 'QA duplica'
            },
            {
                'id': 'ask-for-qa',
                'text': 'QA no duplica'
            }
        ]
    }
    dataset.behave_context = context
    assert map_param("[CONTEXT:list.cmsScrollableActions{1}.id]") == 'ask-for-qa'


def test_a_context_param_list_oob_index():
    """
    Verification of a list with an incorrect index (Out of bounds) as CONTEXT
    """
    class Context(object):
        pass
    context = Context()

    context.list = {
        'cmsScrollableActions': [
            {
                'id': 'ask-for-duplicate',
                'text': 'QA duplica'
            },
            {
                'id': 'ask-for-qa',
                'text': 'QA no duplica'
            }
        ]
    }
    dataset.behave_context = context

    with pytest.raises(Exception) as excinfo:
        map_param("[CONTEXT:list.cmsScrollableActions{2}.id]")
    assert "Invalid index '2', list size is '2'. 2 >= 2." == str(excinfo.value)

    with pytest.raises(Exception) as excinfo:
        map_param("[CONTEXT:list.cmsScrollableActions{5}.id]")
    assert "Invalid index '5', list size is '2'. 5 >= 2." == str(excinfo.value)

def test_a_context_param_list_no_numeric_index():
    """
    Verification of a list with a no numeric index as CONTEXT
    """
    class Context(object):
        pass
    context = Context()

    context.list = {
        'cmsScrollableActions': [
            {
                'id': 'ask-for-duplicate',
                'text': 'QA duplica'
            },
            {
                'id': 'ask-for-qa',
                'text': 'QA no duplica'
            }
        ]
    }
    dataset.behave_context = context

    with pytest.raises(Exception) as excinfo:
        map_param("[CONTEXT:list.cmsScrollableActions{prueba}.id]")
    assert "the index 'prueba' must be a numeric index" == str(excinfo.value)

    with pytest.raises(Exception) as excinfo:
        map_param("[CONTEXT:list.cmsScrollableActions{'36'}.id]")
    assert "the index ''36'' must be a numeric index" == str(excinfo.value)

def test_a_context_param_index_in_non_list_attribute():
    """
    Verification of a index passed in a non list attribute
    """

    class Context(object):
        pass

    context = Context()

    context.list = {
        'url': {
            'id': 'ask-for-duplicate'
        },
        'text': 'QA duplica'
    }
    dataset.behave_context = context
    assert map_param("[CONTEXT:list.url{3}.id{1}]") == 'ask-for-duplicate'
