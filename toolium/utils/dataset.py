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

import os
import re
import datetime
import logging
import random as r
import string
import json
import base64
from ast import literal_eval
from copy import deepcopy
from .data_generator import DataGenerator

logger = logging.getLogger(__name__)


def replace_param(param, language='es', infer_param_type=True):
    """
    Apply transformations to the given param based on specific patterns.
    Available replacements:
        [STRING_WITH_LENGTH_XX] Generates a fixed length string
        [INTEGER_WITH_LENGTH_XX] Generates a fixed length integer
        [STRING_ARRAY_WITH_LENGTH_XX] Generates a fixed length array of strings
        [INTEGER_ARRAY_WITH_LENGTH_XX] Generates a fixed length array of integers
        [JSON_WITH_LENGTH_XX] Generates a fixed length JSON
        [MISSING_PARAM] Generates a None object
        [NULL] Generates a None object
        [TRUE] Generates a boolean True
        [FALSE] Generates a boolean False
        [EMPTY] Generates an empty string
        [B] Generates a blank space
        [RANDOM] Generates a random value
        [RANDOM_PHONE_NUMBER] Generates a random phone number following the pattern +34654XXXXXX
        [TIMESTAMP] Generates a timestamp from the current time
        [DATETIME] Generates a datetime from the current time
        [NOW] Similar to DATETIME without milliseconds; the format depends on the language
        [NOW + 2 DAYS] Similar to NOW but two days later
        [NOW - 1 MINUTES] Similar to NOW but one minute earlier
        [TODAY] Similar to NOW without time; the format depends on the language
        [TODAY + 2 DAYS] Similar to NOW, but two days later
        [STR:xxxx] Cast xxxx to a string
        [INT:xxxx] Cast xxxx to an int
        [FLOAT:xxxx] Cast xxxx to a float
        [LIST:xxxx] Cast xxxx to a list
        [DICT:xxxx] Cast xxxx to a dict
        [UPPER:xxxx] Converts xxxx to upper case
        [LOWER:xxxx] Converts xxxx to lower case
    If infer_param_type is True and the result of the replacement process is a string,
    this function also tries to infer and cast the result to the most appropriate data type,
    attempting first the direct conversion to a Python built-in data type and then,
    if not possible, the conversion to a dict/list parsing the string as a JSON object/list.

    :param param: parameter value
    :param language: language to configure date format for NOW and TODAY ('es' or other)
    :param infer_param_type: whether to infer and change the data type of the result or not
    :return: data with the correct replacements
    """
    if not isinstance(param, str):
        return param

    # Replacements that imply a specific data type and do not admit further transformations
    new_param, param_replaced = _replace_param_type(param)
    if not param_replaced:
        new_param, param_replaced = _replace_param_fixed_length(new_param)

    if not param_replaced:
        # Replacements that return new strings that can be transformed later
        new_param, param_replaced = _replace_param_replacement(new_param, language)
        if not param_replaced:
            new_param, param_replaced = _replace_param_date(new_param, language)

        # String transformations that do not allow type inference
        new_param, param_replaced = _replace_param_transform_string(new_param)

        if not param_replaced and infer_param_type:
            # Type inference
            new_param = _infer_param_type(new_param)

    if param != new_param:
        if type(new_param) == str:
            logger.debug(f'Replaced param from "{param}" to "{new_param}"')
        else:
            logger.debug(f'Replaced param from "{param}" to {new_param}')
    return new_param


def _replace_param_type(param):
    """
    Replace param with a new param type.
    Available replacements: [MISSING_PARAM], [TRUE], [FALSE], [NULL]

    :param param: parameter value
    :return: tuple with replaced value and boolean to know if replacement has been done
    """
    param_types = {
        '[MISSING_PARAM]': None,
        '[TRUE]': True,
        '[FALSE]': False,
        '[NULL]': None
    }
    new_param = param
    param_replaced = False
    for key in param_types.keys():
        if key in param:
            new_param = param_types[key]
            param_replaced = True
            break
    return new_param, param_replaced


def _replace_param_replacement(param, language):
    """
    Replace param with a new param value.
    Available replacements: [EMPTY], [B], [RANDOM], [TIMESTAMP], [DATETIME], [NOW], [TODAY]

    :param param: parameter value
    :param language: language to configure date format for NOW and TODAY
    :return: tuple with replaced value and boolean to know if replacement has been done
    """
    date_format = '%d/%m/%Y %H:%M:%S' if language == 'es' else '%Y/%m/%d %H:%M:%S'
    date_day_format = '%d/%m/%Y' if language == 'es' else '%Y/%m/%d'
    alphanums = ''.join([string.ascii_lowercase, string.digits])  # abcdefghijklmnopqrstuvwxyz0123456789
    replacements = {
        '[EMPTY]': '',
        '[B]': ' ',
        # make sure random is not made up of digits only, by forcing the first char to be a letter
        '[RANDOM]': ''.join([r.choice(string.ascii_lowercase), *(r.choice(alphanums) for i in range(7))]),
        '[RANDOM_PHONE_NUMBER]': DataGenerator().phone_number,
        '[TIMESTAMP]': str(int(datetime.datetime.timestamp(datetime.datetime.utcnow()))),
        '[DATETIME]': str(datetime.datetime.utcnow()),
        '[NOW]': str(datetime.datetime.utcnow().strftime(date_format)),
        '[TODAY]': str(datetime.datetime.utcnow().strftime(date_day_format))
    }
    new_param = param
    param_replaced = False
    for key in replacements.keys():
        if key in param:
            new_param = param.replace(key, replacements[key])
            param_replaced = True
            break
    return new_param, param_replaced


def _replace_param_transform_string(param):
    """
    Transform param value according to the specified prefix.
    Available transformations: DICT, LIST, INT, FLOAT, STR, UPPER, LOWER

    :param param: parameter value
    :return: tuple with replaced value and boolean to know if replacement has been done
    """
    type_mapping_regex = r'\[(DICT|LIST|INT|FLOAT|STR|UPPER|LOWER):(.*)\]'
    type_mapping_match_group = re.match(type_mapping_regex, param)
    new_param = param
    param_transformed = False

    if type_mapping_match_group:
        param_transformed = True
        if type_mapping_match_group.group(1) == 'STR':
            new_param = type_mapping_match_group.group(2)
        elif type_mapping_match_group.group(1) in ['LIST', 'DICT', 'INT', 'FLOAT']:
            exec('exec_param = {type}({value})'.format(type=type_mapping_match_group.group(1).lower(),
                                                       value=type_mapping_match_group.group(2)))
            new_param = locals()['exec_param']
        elif type_mapping_match_group.group(1) == 'UPPER':
            new_param = type_mapping_match_group.group(2).upper()
        elif type_mapping_match_group.group(1) == 'LOWER':
            new_param = type_mapping_match_group.group(2).lower()
    return new_param, param_transformed


def _replace_param_date(param, language):
    """
    Transform param value in a date after applying the specified delta.
    E.g. [TODAY - 2 DAYS], [NOW - 10 MINUTES]

    :param param: parameter value
    :param language: language to configure date format for NOW and TODAY
    :return: tuple with replaced value and boolean to know if replacement has been done
    """
    date_format = '%d/%m/%Y %H:%M:%S' if language == 'es' else '%Y/%m/%d %H:%M:%S'
    date_day_format = '%d/%m/%Y' if language == 'es' else '%Y/%m/%d'
    date_matcher = re.match(r'\[(NOW|TODAY)\s*([\+|-]\s*\d+)\s*(\w+)\s*\]', param)
    new_param = param
    param_replaced = False

    if date_matcher and len(date_matcher.groups()) == 3:
        configuration = dict([(date_matcher.group(3).lower(), int(date_matcher.group(2).replace(' ', '')))])
        now = (date_matcher.group(1) == 'NOW')
        reference_date = datetime.datetime.utcnow() if now else datetime.datetime.utcnow().date()
        replace_value = reference_date + datetime.timedelta(**configuration)
        new_param = replace_value.strftime(date_format) if now else replace_value.strftime(date_day_format)
        param_replaced = True
    return new_param, param_replaced


def _replace_param_fixed_length(param):
    """
    Generate a fixed length data element if param matches the expression [<type>_WITH_LENGTH_<length>]
    where <type> can be: STRING, INTEGER, STRING_ARRAY, INTEGER_ARRAY, JSON.
    E.g. [STRING_WITH_LENGTH_15]

    :param param: parameter value
    :return: tuple with replaced value and boolean to know if replacement has been done
    """
    new_param = param
    param_replaced = False
    if param.startswith('[') and param.endswith(']'):
        if any(x in param for x in ['STRING_ARRAY_WITH_LENGTH_', 'INTEGER_ARRAY_WITH_LENGTH_']):
            seeds = {'STRING': 'a', 'INTEGER': 1}
            seed, length = param[1:-1].split('_ARRAY_WITH_LENGTH_')
            new_param = list(seeds[seed] for x in range(int(length)))
            param_replaced = True
        elif 'JSON_WITH_LENGTH_' in param:
            length = int(param[1:-1].split('JSON_WITH_LENGTH_')[1])
            new_param = dict((str(x), str(x)) for x in range(length))
            param_replaced = True
        elif any(x in param for x in ['STRING_WITH_LENGTH_', 'INTEGER_WITH_LENGTH_']):
            seeds = {'STRING': 'a', 'INTEGER': '1'}
            # The chain to be generated can be just a part of param
            start = param.find('[')
            end = param.find(']')
            seed, length = param[start + 1:end].split('_WITH_LENGTH_')
            generated_part = seeds[seed] * int(length)
            placeholder = '[' + seed + '_WITH_LENGTH_' + length + ']'
            new_param = param.replace(placeholder, generated_part)
            param_replaced = True
            if seed == 'INTEGER':
                new_param = int(new_param)
    return new_param, param_replaced


def _infer_param_type(param):
    """
    Transform the param from a string representing a built-in data type or a JSON object/list to the
    corresponding built-in data type. If no conversion is possible, the original param is returned.
    E.g. "1234" -> 1234, "0.50" -> 0.5, "True" -> True, "None" -> None,
    "['a', None]" -> ['a', None], "{'a': None}" -> {'a': None},
    '["a", null]' -> ["a", None], '{"a": null}' -> {"a": None}

    :param param: data to be transformed
    :return data with the inferred type
    """
    new_param = param
    # attempt direct conversion to a built-in data type
    try:
        new_param = literal_eval(param)
    except Exception:
        # it may still be a JSON object/list that can be converted to a dict/list
        try:
            if param.startswith('{') or param.startswith('['):
                new_param = json.loads(param)
        except Exception:
            pass
    return new_param


def map_param(param, context=None):
    """
    Transform the given string by replacing specific patterns containing keys with their values,
    which can be obtained from the Behave context or from environment files or variables.
    See map_one_param function for a description of the available tags and replacement logic.

    :param param: string parameter
    :param context: Behave context object
    :return: string with the applied replacements
    """
    if not isinstance(param, str):
        return param

    map_regex = r"[\[CONF:|\[LANG:|\[POE:|\[ENV:|\[BASE64:|\[TOOLIUM:|\[CONTEXT:|\[FILE:][a-zA-Z\.\:\/\_\-\ 0-9]*\]"
    map_expressions = re.compile(map_regex)

    # The parameter is just one config value
    if map_expressions.split(param) == ['', '']:
        return map_one_param(param, context)

    # The parameter is a combination of text and configuration parameters.
    for match in map_expressions.findall(param):
        param = param.replace(match, str(map_one_param(match, context)))
    return param


def map_one_param(param, context=None):
    """
    Analyze the pattern in the given string and find out its transformed value.
    Available tags and replacement values:
        [CONF:xxxx] Value from the config dict in context.project_config for the key xxxx (dot notation is used
        for keys, e.g. key_1.key_2.0.key_3)
        [LANG:xxxx] String from the texts dict in context.language_dict for the key xxxx, using the language
        specified in context.language (dot notation is used for keys, e.g. button.label)
        [POE:xxxx] Definition(s) from the POEditor terms list in context.poeditor_terms for the term xxxx
        [TOOLIUM:xxxx] Value from the toolium config in context.toolium_config for the key xxxx (key format is
        section_option, e.g. Driver_type)
        [CONTEXT:xxxx] Value from the context storage dict for the key xxxx, or value of the context attribute xxxx,
        if the former does not exist
        [ENV:xxxx] Value of the OS environment variable xxxx
        [FILE:xxxx] String with the content of the file in the path xxxx
        [BASE64:xxxx] String with the base64 representation of the file content in the path xxxx

    :param param: string parameter
    :param context: Behave context object
    :return: transformed value or the original string if no transformation could be applied
    """
    if not isinstance(param, str):
        return param

    type, key = _get_mapping_type_and_key(param)

    mapping_functions = {
        "CONF": {
            "prerequisites": context and hasattr(context, "project_config"),
            "function": map_json_param,
            "args": [key, context.project_config if hasattr(context, "project_config") else None]
        },
        "TOOLIUM": {
            "prerequisites": context,
            "function": map_toolium_param,
            "args": [key, context]
        },
        "CONTEXT": {
            "prerequisites": context,
            "function": get_value_from_context,
            "args": [key, context]
        },
        "LANG": {
            "prerequisites": context,
            "function": get_message_property,
            "args": [key, context]
        },
        "POE": {
            "prerequisites": context,
            "function": get_translation_by_poeditor_reference,
            "args": [key, context]
        },
        "ENV": {
            "prerequisites": True,
            "function": os.environ.get,
            "args": [key]
        },
        "FILE": {
            "prerequisites": True,
            "function": get_file,
            "args": [key]
        },
        "BASE64": {
            "prerequisites": True,
            "function": convert_file_to_base64,
            "args": [key]
        }
    }

    if key and mapping_functions[type]["prerequisites"]:
        return mapping_functions[type]["function"](*mapping_functions[type]["args"])
    else:
        return param


def _get_mapping_type_and_key(param):
    """
    Get the type and the key of the given string parameter to be mapped to the appropriate value.

    :param param: string parameter to be parsed
    :return: a tuple with the type and the key to be mapped
    """
    types = ["CONF", "LANG", "POE", "ENV", "BASE64", "TOOLIUM", "CONTEXT", "FILE"]
    for type in types:
        match_group = re.match(r"\[%s:(.*)\]" % type, param)
        if match_group:
            return type, match_group.group(1)
    return None, None


def map_json_param(param, config, copy=True):
    """
    Find the value of the given param using it as a key in the given dictionary. Dot notation is used,
    so for example "service.vamps.user" could be used to retrieve the email in the following config example:
    {
        "services":{
            "vamps":{
                "user": "cyber-sec-user@11paths.com",
                "password": "MyPassword"
            }
        }
    }

    :param param: key to be searched (dot notation is used, e.g. "service.vamps.user").
    :param config: configuration dictionary
    :param copy: boolean value to indicate whether to work with a copy of the given dictionary or not,
    in which case, the dictionary content might be changed by this function (True by default)
    :return: mapped value
    """
    properties_list = param.split(".")
    aux_config_json = deepcopy(config) if copy else config
    try:
        for property in properties_list:
            if type(aux_config_json) is list:
                aux_config_json = aux_config_json[int(property)]
            else:
                aux_config_json = aux_config_json[property]

        hidden_value = hide_passwords(param, aux_config_json)
        logger.debug(f"Mapping param '{param}' to its configured value '{hidden_value}'")
    except TypeError:
        msg = f"Mapping chain not found in the given configuration dictionary. '{param}'"
        logger.error(msg)
        raise TypeError(msg)
    except KeyError:
        msg = f"Mapping chain not found in the given configuration dictionary. '{param}'"
        logger.error(msg)
        raise KeyError(msg)
    except ValueError:
        msg = f"Specified value is not a valid index. '{param}'"
        logger.error(msg)
        raise ValueError(msg)
    except IndexError:
        msg = f"Mapping index not found in the given configuration dictionary. '{param}'"
        logger.error(msg)
        raise IndexError(msg)
    return os.path.expandvars(aux_config_json) \
        if aux_config_json and type(aux_config_json) not in [int, bool, float, list, dict] else aux_config_json


def hide_passwords(key, value):
    """
    Return asterisks when the given key is a password that should be hidden.

    :param key: key name
    :param value: value
    :return: hidden value
    """
    hidden_keys = ['key', 'pass', 'secret', 'code', 'token']
    hidden_value = '*****'
    return hidden_value if any(hidden_key in key for hidden_key in hidden_keys) else value


def map_toolium_param(param, context):
    """
    Find the value of the given param using it as a key in the current toolium configuration (context.toolium_config).
    The param is expected to be in the form <section>_<property>, so for example "TextExecution_environment" could be
    used to retrieve the value of this toolium property (i.e. the string "QA"):
    [TestExecution]
    environment: QA

    :param param: key to be searched (e.g. "TextExecution_environment")
    :param context: Behave context object
    :return: mapped value
    """
    try:
        section = param.split("_", 1)[0]
        property_name = param.split("_", 1)[1]
    except IndexError:
        msg = f"Invalid format in Toolium config param '{param}'. Valid format: 'Section_property'."
        logger.error(msg)
        raise IndexError(msg)

    try:
        mapped_value = context.toolium_config.get(section, property_name)
        logger.info(f"Mapping Toolium config param 'param' to its configured value '{mapped_value}'")
    except Exception:
        msg = f"'{param}' param not found in Toolium config file"
        logger.error(msg)
        raise Exception(msg)
    return mapped_value


def get_value_from_context(param, context):
    """
    Find the value of the given param using it as a key in the context storage dictionary (context.storage) or in the
    context object itself. So for example, in the former case, "last_request_result" could be used to retrieve the value
    from context.storage["last_request_result"], if it exists, whereas, in the latter case, "last_request.result" could
    be used to retrieve the value from context.last_request.result, if it exists.

    :param param: key to be searched (e.g. "last_request_result" / "last_request.result")
    :param context: Behave context object
    :return: mapped value
    """
    if context.storage and param in context.storage:
        return context.storage[param]
    logger.info(f"'{param}' key not found in context storage, searching in context")
    try:
        value = context
        for part in param.split('.'):
            value = getattr(value, part)
        return value
    except AttributeError:
        msg = f"'{param}' not found neither in context storage nor in context"
        logger.error(msg)
        raise AttributeError(msg)


def get_message_property(param, context):
    """
    Return the message for the given param, using it as a key in the list of language properties previously loaded
    in the context (context.language_dict). Dot notation is used (e.g. "home.button.send").

    :param param: message key
    :param context: Behave context object
    :return: the message mapped to the given key in the language set in the context (context.language)
    """
    key_list = param.split(".")
    language_dict_copy = deepcopy(context.language_dict)
    try:
        for key in key_list:
            language_dict_copy = language_dict_copy[key]
        logger.info(f"Mapping language param '{param}' to its configured value '{language_dict_copy[context.language]}'")
    except KeyError:
        msg = f"Mapping chain '{param}' not found in the language properties file"
        logger.error(msg)
        raise KeyError(msg)

    return language_dict_copy[context.language]


def get_translation_by_poeditor_reference(reference, context):
    """
    Return the translation(s) for the given POEditor reference from the terms previously loaded in the context.

    :param reference: POEditor reference
    :param context: Behave context object
    :return: list of strings with the translations from POEditor or string with the translation if only one was found
    """
    try:
        context.poeditor_terms = context.poeditor_export
    except AttributeError:
        raise Exception("POEditor texts haven't been correctly downloaded!")
    poeditor_conf = context.project_config['poeditor'] if 'poeditor' in context.project_config else {}
    key = poeditor_conf['key_field'] if 'key_field' in poeditor_conf else 'reference'
    search_type = poeditor_conf['search_type'] if 'search_type' in poeditor_conf else 'contains'
    # Get POEditor prefixes and add no prefix option
    poeditor_prefixes = poeditor_conf['prefixes'] if 'prefixes' in poeditor_conf else []
    poeditor_prefixes.append('')
    for prefix in poeditor_prefixes:
        if len(reference.split(':')) > 1 and prefix != '':
            # If there are prefixes and the resource contains ':' apply prefix in the correct position
            complete_reference = '%s:%s%s' % (reference.split(':')[0], prefix, reference.split(':')[1])
        else:
            complete_reference = '%s%s' % (prefix, reference)
        if search_type == 'exact':
            translation = [term['definition'] for term in context.poeditor_terms
                           if complete_reference == term[key] and term['definition'] is not None]
        else:
            translation = [term['definition'] for term in context.poeditor_terms
                           if complete_reference in term[key] and term['definition'] is not None]
        if len(translation) > 0:
            break
    assert len(translation) > 0, 'No translations found in POEditor for reference %s' % reference
    translation = translation[0] if len(translation) == 1 else translation
    return translation


def get_file(file_path):
    """
    Return the content of a file given its path.

    :param file path: file path using slash as separator (e.g. "resources/files/doc.txt")
    :return: string with the file content
    """
    file_path_parts = file_path.split("/")
    file_path = os.path.join(*file_path_parts)
    if not os.path.exists(file_path):
        raise Exception(f' ERROR - Cannot read file "{file_path}". Does not exist.')

    with open(file_path, 'r') as f:
        return f.read()


def convert_file_to_base64(file_path):
    """
    Return the content of a file given its path encoded in Base64.

    :param file path: file path using slash as separator (e.g. "resources/files/doc.txt")
    :return: string with the file content encoded in Base64
    """
    file_path_parts = file_path.split("/")
    file_path = os.path.join(*file_path_parts)
    if not os.path.exists(file_path):
        raise Exception(f' ERROR - Cannot read file "{file_path}". Does not exist.')

    try:
        with open(file_path, "rb") as f:
            file_content = base64.b64encode(f.read()).decode()
    except Exception as e:
        raise Exception(f' ERROR - converting the "{file_path}" file to Base64...: {e}')
    return file_content
