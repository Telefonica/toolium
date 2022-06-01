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
from toolium.utils import dataset
from toolium.utils.dataset import map_param, set_base64_path, set_file_path, hide_passwords


def test_an_env_param():
    """
    Verification of a mapped parameter as ENV
    """
    os.environ['MY_PASSWD'] = "admin123"
    result = map_param("[ENV:MY_PASSWD]")
    expected = "admin123"
    assert expected == result


def test_a_file_param():
    """
    Verification of a mapped parameter as FILE
    """
    result = map_param("[FILE:toolium/test/resources/document.txt]")
    expected = "Document used to verify functionalities in MSS "
    assert expected == result
    set_file_path('toolium/test/resources/')
    result = map_param("[FILE:document.txt]")
    assert expected == result


def test_a_base64_param():
    """
    Verification of a mapped parameter as BASE64
    """
    result = map_param("[BASE64:toolium/test/resources/document.txt]")
    expected = "RG9jdW1lbnQgdXNlZCB0byB2ZXJpZnkgZnVuY3Rpb25hbGl0aWVzIGluIE1TUyA="
    assert expected == result
    set_base64_path('toolium/test/resources/')
    result = map_param("[BASE64:document.txt]")
    assert expected == result


def test_a_lang_param():
    """
    Verification of a mapped parameter as LANG
    """
    dataset.language_terms = {"home": {"button": {"send": {"es": "enviar", "en": "send"}}}}
    dataset.language = "es"
    result = map_param("[LANG:home.button.send]")
    expected = "enviar"
    assert expected == result


def test_a_toolium_param():
    """
    Verification of a mapped parameter as TOOLIUM
    """
    config_file_path = os.path.join("toolium", "test", "resources", "toolium.cfg")
    dataset.toolium_config = ExtendedConfigParser.get_config_from_file(config_file_path)
    result = map_param("[TOOLIUM:TestExecution_environment]")
    expected = "QA"
    assert expected == result


def test_a_conf_param():
    """
    Verification of a mapped parameter as CONF
    """
    dataset.project_config = {"service": {"port": 80}}
    result = map_param("[CONF:service.port]")
    expected = 80
    assert expected == result


def test_a_context_param():
    """
    Verification of a mapped parameter as CONTEXT
    """
    context = mock.MagicMock()
    context.attribute = "attribute value"
    context.storage = {"storage_key": "storage entry value"}
    dataset.behave_context = context

    result_att = map_param("[CONTEXT:attribute]")
    expected_att = "attribute value"
    assert expected_att == result_att
    result_st = map_param("[CONTEXT:storage_key]")
    expected_st = "storage entry value"
    assert expected_st == result_st


def test_a_context_param_with_dots():
    """
    Verification of a mapped parameter with dots as CONTEXT
    """
    context = mock.MagicMock()

    class Obj(object):
        pass
    one = Obj()
    one.two = "the value"

    context.one = one
    dataset.behave_context = context

    result_att = map_param("[CONTEXT:one.two]")
    expected_att = "the value"
    assert expected_att == result_att

    three = Obj()
    three.four = "the other value"

    context.storage = {"three": three}
    dataset.behave_context = context

    result_att = map_param("[CONTEXT:three.four]")
    expected_att = "the other value"
    assert expected_att == result_att


def test_a_context_param_deprecated():
    """
    Verification of a mapped parameter as CONTEXT and check that deprecated message is logged
    """
    context = mock.MagicMock()
    context.attribute = "attribute value"
    dataset.logger = mock.MagicMock()

    result_att = map_param("[CONTEXT:attribute]", context)
    expected_att = "attribute value"
    assert expected_att == result_att
    dataset.logger.warning.assert_called_with("Deprecated context parameter has been sent to map_param method. Please, "
                                              "configure dataset global variables instead of passing context to "
                                              "map_param.")


def test_a_poe_param_single_result():
    """
    Verification of a POE mapped parameter with a single result for a reference
    """
    dataset.poeditor_terms = [
        {
            "term": "Poniendo mute",
            "definition": "Ahora la tele está silenciada",
            "reference": "home:home.tv.mute",
        }
    ]
    result = map_param('[POE:home.tv.mute]')
    expected = "Ahora la tele está silenciada"
    assert result == expected


def test_a_poe_param_single_result_deprecated():
    """
    Verification of a POE mapped parameter with a single result for a reference
    """
    context = mock.MagicMock()
    context.poeditor_export = [
        {
            "term": "Poniendo mute",
            "definition": "Ahora la tele está silenciada",
            "reference": "home:home.tv.mute",
        }
    ]
    dataset.logger = mock.MagicMock()

    result = map_param('[POE:home.tv.mute]', context)
    expected = "Ahora la tele está silenciada"
    assert result == expected
    dataset.logger.warning.assert_called_with("Deprecated context parameter has been sent to map_param method. Please, "
                                              "configure dataset global variables instead of passing context to "
                                              "map_param.")


def test_a_poe_param_no_result_assertion():
    """
    Verification of a POE mapped parameter without result
    """
    dataset.poeditor_terms = [
        {
            "term": "Poniendo mute",
            "definition": "Ahora la tele está silenciada",
            "reference": "home:home.tv.mute",
        }
    ]
    with pytest.raises(Exception) as excinfo:
        map_param('[POE:home.tv.off]')
    assert "No translations found in POEditor for reference home.tv.off" in str(excinfo.value)


def test_a_poe_param_prefix_with_no_definition():
    """
    Verification of a POE mapped parameter with a single result for a reference
    """
    dataset.project_config = {'poeditor': {'key_field': 'reference', 'search_type': 'contains', 'prefixes': ['PRE.']}}
    dataset.poeditor_terms = [
        {
            "term": "Hola, estoy aquí para ayudarte",
            "definition": None,
            "reference": "common:PRE.common.greetings.main",
        },
        {
            "term": "Hola! En qué puedo ayudarte?",
            "definition": "Hola, buenas",
            "reference": "common:common.greetings.main",
        }
    ]
    result = map_param('[POE:common:common.greetings.main]')
    expected = "Hola, buenas"
    assert result == expected


def test_a_poe_param_single_result_selecting_a_key_field():
    """
    Verification of a POE mapped parameter with a single result for a term
    """
    dataset.project_config = {'poeditor': {'key_field': 'term'}}
    dataset.poeditor_terms = [
        {
            "term": "loginSelectLine_text_subtitle",
            "definition": "Te damos la bienvenida",
            "context": "",
            "term_plural": "",
            "reference": "",
            "comment": ""
        }
    ]
    result = map_param('[POE:loginSelectLine_text_subtitle]')
    expected = "Te damos la bienvenida"
    assert result == expected


def test_a_poe_param_multiple_results():
    """
    Verification of a POE mapped parameter with several results for a reference
    """
    dataset.project_config = {'poeditor': {'key_field': 'reference'}}
    dataset.poeditor_terms = [
        {
            "term": "Hola, estoy aquí para ayudarte",
            "definition": "Hola, estoy aquí para ayudarte",
            "reference": "common:common.greetings.main",
        },
        {
            "term": "Hola! En qué puedo ayudarte?",
            "definition": "Hola, buenas",
            "reference": "common:common.greetings.main",
        }
    ]
    result = map_param('[POE:common.greetings.main]')
    first_expected = "Hola, estoy aquí para ayudarte"
    second_expected = "Hola, buenas"
    assert len(result) == 2
    assert result[0] == first_expected
    assert result[1] == second_expected


def test_a_poe_param_multiple_options_but_only_one_result():
    """
    Verification of a POE mapped parameter with a single result from several options for a key
    """
    dataset.project_config = {'poeditor': {'key_field': 'term', 'search_type': 'exact'}}
    dataset.poeditor_terms = [
        {
            "term": "loginSelectLine_text_subtitle",
            "definition": "Te damos la bienvenida_1",
            "context": "",
            "term_plural": "",
            "reference": "",
            "comment": ""
        },
        {
            "term": "loginSelectLine_text_subtitle_2",
            "definition": "Te damos la bienvenida_2",
            "context": "",
            "term_plural": "",
            "reference": "",
            "comment": ""
        }
    ]
    result = map_param('[POE:loginSelectLine_text_subtitle]')
    expected = "Te damos la bienvenida_1"
    assert result == expected


def test_a_poe_param_with_prefix():
    """
    Verification of a POE mapped parameter with several results for a reference, filtered with a prefix
    """
    dataset.project_config = {'poeditor': {'key_field': 'reference', 'search_type': 'contains', 'prefixes': ['PRE.']}}
    dataset.poeditor_terms = [
        {
            "term": "Hola, estoy aquí para ayudarte",
            "definition": "Hola, estoy aquí para ayudarte",
            "reference": "common:common.greetings.main",
        },
        {
            "term": "Hola! En qué puedo ayudarte?",
            "definition": "Hola, buenas",
            "reference": "common:PRE.common.greetings.main",
        }
    ]
    result = map_param('[POE:common.greetings.main]')
    expected = "Hola, buenas"
    assert result == expected


def test_a_poe_param_with_two_prefixes():
    """
    Verification of a POE mapped parameter with several results for a reference, filtered with two prefixes
    """
    dataset.project_config = {'poeditor': {'prefixes': ['MH.', 'PRE.']}}
    dataset.poeditor_terms = [
        {
            "term": "Hola, estoy aquí para ayudarte",
            "definition": "Hola, estoy aquí para ayudarte",
            "reference": "common:common.greetings.main",
        },
        {
            "term": "Hola! En qué puedo ayudarte?",
            "definition": "Hola, buenas",
            "reference": "common:PRE.common.greetings.main",
        },
        {
            "term": "Hola! En qué puedo ayudarte MH?",
            "definition": "Hola, buenas MH",
            "reference": "common:MH.common.greetings.main",
        }
    ]
    result = map_param('[POE:common.greetings.main]')
    expected = "Hola, buenas MH"
    assert result == expected


def test_a_poe_param_with_prefix_and_exact_resource():
    """
    Verification of a POE mapped parameter that uses an exact resource name and has a prefix configured
    """
    dataset.project_config = {'poeditor': {'prefixes': ['PRE.']}}
    dataset.poeditor_terms = [
        {
            "term": "Hola, estoy aquí para ayudarte",
            "definition": "Hola, estoy aquí para ayudarte",
            "reference": "common:common.greetings.main",
        },
        {
            "term": "Hola! En qué puedo ayudarte?",
            "definition": "Hola, buenas",
            "reference": "common:PRE.common.greetings.main",
        }
    ]
    result = map_param('[POE:common:common.greetings.main]')
    expected = "Hola, buenas"
    assert result == expected


def test_a_text_param():
    """
    Verification of a text param
    """
    result = map_param("just_text")
    expected = "just_text"
    assert expected == result


def test_a_combi_of_textplusconfig():
    """
    Verification of a combination of text plus a config param
    """
    os.environ['MY_VAR'] = "some value"
    result = map_param("adding [ENV:MY_VAR]")
    expected = "adding some value"
    assert expected == result


def test_a_combi_of_textplusconfig_integer():
    """
    Verification of a combination of text plus a config param
    """
    dataset.project_config = {"service": {"port": 80}}
    result = map_param("use port [CONF:service.port]")
    expected = "use port 80"
    assert expected == result


def test_a_combi_of_configplusconfig():
    """
    Verification of a combination of a config param plus a config param
    """
    os.environ['MY_VAR_1'] = "this is "
    os.environ['MY_VAR_2'] = "some value"
    result = map_param("[ENV:MY_VAR_1][ENV:MY_VAR_2]")
    expected = "this is some value"
    assert expected == result


def test_a_combi_of_config_plustext_plusconfig():
    """
    Verification of a combination of a config param plus text plus a config param
    """
    os.environ['MY_VAR_1'] = "this is"
    os.environ['MY_VAR_2'] = "some value"
    result = map_param("[ENV:MY_VAR_1] some text and [ENV:MY_VAR_2]")
    expected = "this is some text and some value"
    assert expected == result


def test_a_combi_of_config_inside_config():
    """
    Verification of a combination of a config param inside another config param
    """
    dataset.project_config = {"var_name": "NAME2"}
    os.environ['MY_VAR_NAME1'] = "name1 value"
    os.environ['MY_VAR_NAME2'] = "name2 value"
    result = map_param("[ENV:MY_VAR_[CONF:var_name]]")
    expected = "name2 value"
    assert expected == result


def test_a_combi_of_config_inside_config_recursively():
    """
    Verification of a combination of a config param inside another config param recursively
    """
    dataset.project_config = {"var_number": 2, "var_name_1": "A", "var_name_2": "B"}
    os.environ['MY_VAR_A'] = "A value"
    os.environ['MY_VAR_B'] = "B value"
    result = map_param("[CONF:var_number] some text [ENV:MY_VAR_[CONF:var_name_[CONF:var_number]]]")
    expected = "2 some text B value"
    assert expected == result


def test_a_conf_param_with_special_characters():
    """
    Verification of a combination of text plus a config param with special characters
    """
    dataset.project_config = {"user": "user-1", "password": "p4:ssw0_rd"}
    result = map_param("[CONF:user]-an:d_![CONF:password]")
    expected = "user-1-an:d_!p4:ssw0_rd"
    assert expected == result


# Data input for hide_passwords
hide_passwords_data = [
    ('name', 'value', 'value'),
    ('key', 'value', '*****'),
    ('second_key', 'value', '*****'),
    ('pas', 'value', 'value'),
    ('pass', 'value', '*****'),
    ('password', 'value', '*****'),
    ('secret', 'value', '*****'),
    ('code', 'value', '*****'),
    ('token', 'value', '*****'),
]


@pytest.mark.parametrize("key,value,hidden_value", hide_passwords_data)
def test_hide_passwords(key, value, hidden_value):
    assert hidden_value == hide_passwords(key, value)
