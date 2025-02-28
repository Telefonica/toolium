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

import base64
import collections
import datetime
import json
import logging
import os
import random as r
import re
import string
import uuid

from ast import literal_eval
from copy import deepcopy
from inspect import isfunction
from toolium.utils.data_generator import DataGenerator

logger = logging.getLogger(__name__)

# Base path for BASE64 and FILE conversions
base_base64_path = ''
base_file_path = ''

# Global variables used in map_param replacements

# Language terms, country and project config are not set by toolium, they must be set from test project
language = None
language_terms = None
country = None
project_config = None
# Toolium config and behave context are set when toolium before_all method is called in behave tests
toolium_config = None
behave_context = None
# POEditor terms are set when load_poeditor_texts or export_poeditor_project poeditor.py methods are called
poeditor_terms = None


def replace_param(param, language='es', infer_param_type=True):
    """
    Apply transformations to the given param based on specific patterns.
    Available replacements:

    - [STRING_WITH_LENGTH_XX] Generates a fixed length string
    - [INTEGER_WITH_LENGTH_XX] Generates a fixed length integer
    - [STRING_ARRAY_WITH_LENGTH_XX] Generates a fixed length array of strings
    - [INTEGER_ARRAY_WITH_LENGTH_XX] Generates a fixed length array of integers
    - [JSON_WITH_LENGTH_XX] Generates a fixed length JSON
    - [MISSING_PARAM] Generates a None object
    - [NULL] Generates a None object
    - [TRUE] Generates a boolean True
    - [FALSE] Generates a boolean False
    - [EMPTY] Generates an empty string
    - [B] Generates a blank space
    - [UUID] Generates a v4 UUID
    - [RANDOM] Generates a random value
    - [RANDOM_PHONE_NUMBER] Generates a random phone number for language and country configured
      in dataset.language and dataset.country
    - [TIMESTAMP] Generates a timestamp from the current time
    - [DATETIME] Generates a datetime from the current time (UTC)
    - [NOW] Similar to DATETIME without microseconds; the format depends on the language
    - [NOW(%Y-%m-%dT%H:%M:%SZ)] Same as NOW but using an specific format by the python strftime function of
      the datetime module. In the case of the %f placeholder, the syntax has been extended to allow setting
      an arbitrary number of digits (e.g. %3f would leave just the 3 most significant digits and truncate the rest)
    - [NOW + 2 DAYS] Similar to NOW but two days later
    - [NOW - 1 MINUTES] Similar to NOW but one minute earlier
    - [NOW(%Y-%m-%dT%H:%M:%SZ) - 7 DAYS] Similar to NOW but seven days before and with the indicated format
    - [TODAY] Similar to NOW without time; the format depends on the language
    - [TODAY + 2 DAYS] Similar to NOW, but two days later
    - [ROUND:xxxx::y] Generates a string from a float number (xxxx) with the indicated number of decimals (y)
    - [STR:xxxx] Cast xxxx to a string
    - [INT:xxxx] Cast xxxx to an int
    - [FLOAT:xxxx] Cast xxxx to a float
    - [LIST:xxxx] Cast xxxx to a list
    - [DICT:xxxx] Cast xxxx to a dict
    - [UPPER:xxxx] Converts xxxx to upper case
    - [LOWER:xxxx] Converts xxxx to lower case
    - [REPLACE:xxxxx::yy::zz] Replace elements in string. Example: [REPLACE:[CONTEXT:some_url]::https::http]
    - [TITLE:xxxxx] Apply .title() to string value. Example: [TITLE:the title]

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
        new_param, _ = _replace_param_replacement(new_param, language)

        # String transformations that do not allow type inference
        new_param, param_replaced = _replace_param_transform_string(new_param)

        if not param_replaced and infer_param_type:
            # Type inference
            new_param = _infer_param_type(new_param)

    if param != new_param:
        if isinstance(new_param, str):
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


def _find_param_date_expressions(param):
    """
    Finds in a param one or several date expressions.
    For example, for a param like "it happened on [NOW - 1 MONTH] of the last year and will happen [TODAY('%d/%m')]",
    this method returns an array with two string elements: "[NOW - 1 MONTH]" and [TODAY('%d/%m')]"
    The kind of expressions to search are based on these rules:
    - expression is sorrounded by [ and ]
    - first word of the expression is either NOW or TODAY
    - when first word is NOW, it can have an addtional format for the date between parenthesis,
        like NOW(%Y-%m-%dT%H:%M:%SZ). The definition of the format is the same as considered by the
        python strftime function of the datetime module
    - and optional offset can be given by indicating how many days, hours, etc.. to add or remove to the current
        datetime. This part of the expression includes a +/- symbol plus a number and a unit

    Some valid expressions are:
        [NOW]
        [TODAY]
        [NOW(%Y-%m-%dT%H:%M:%SZ)]
        [NOW(%Y-%m-%dT%H:%M:%SZ) - 180 DAYS]
        [NOW(%H:%M:%S) + 4 MINUTES]

    :param param: parameter value
    :param language: language to configure date format for NOW and TODAY
    :return: An array with all the matching date expressions found in the param
    """
    return re.findall(r"\[(?:NOW(?:\((?:[^\(\)]*)\))?|TODAY)(?:\s*[\+|-]\s*\d+\s*\w+\s*)?\]", param)


def _replace_param_replacement(param, language):
    """
    Replace param with a new param value.
    Available replacements: [EMPTY], [B], [UUID], [RANDOM], [RANDOM_PHONE_NUMBER],
                            [TIMESTAMP], [DATETIME], [NOW], [TODAY], [ROUND:xxxxx::d]

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
        '[UUID]': str(uuid.uuid4()),
        # make sure random is not made up of digits only, by forcing the first char to be a letter
        '[RANDOM]': ''.join([r.choice(string.ascii_lowercase), *(r.choice(alphanums) for i in range(7))]),
        '[RANDOM_PHONE_NUMBER]': _get_random_phone_number,
        '[TIMESTAMP]': str(int(datetime.datetime.timestamp(datetime.datetime.utcnow()))),
        '[DATETIME]': str(datetime.datetime.utcnow()),
        '[NOW]': str(datetime.datetime.utcnow().strftime(date_format)),
        '[TODAY]': str(datetime.datetime.utcnow().strftime(date_day_format)),
        r'\[ROUND:(.*?)::(\d*)\]': _get_rounded_float_number
    }

    # append date expressions found in param to the replacement dict
    date_expressions = _find_param_date_expressions(param)
    for date_expr in date_expressions:
        replacements[date_expr] = _replace_param_date(date_expr, language)[0]

    new_param = param
    param_replaced = False
    for key, value in replacements.items():
        if key.startswith('['):  # tags without placeholders
            if key in new_param:
                new_value = value() if isfunction(value) else value
                new_param = new_param.replace(key, new_value)
                param_replaced = True
        elif match := re.search(key, new_param):  # tags with placeholders
            new_value = value(match)  # a function to parse the values is always required
            new_param = new_param.replace(match.group(), new_value)
            param_replaced = True
    return new_param, param_replaced


def _get_rounded_float_number(match):
    """
    Round float number with the expected decimals
    :param match: match object of the regex for this transformation: [ROUND:(.*?)::(d*)]
    :return: float as string with the expected decimals
    """
    return f"{round(float(match.group(1)), int(match.group(2))):.{int(match.group(2))}f}"


def _get_random_phone_number():
    # Method to avoid executing data generator when it is not needed
    return DataGenerator().phone_number


def _replace_param_transform_string(param):
    """
    Transform param value according to the specified prefix.
    Available transformations: DICT, LIST, INT, FLOAT, STR, UPPER, LOWER, REPLACE, TITLE

    :param param: parameter value
    :return: tuple with replaced value and boolean to know if replacement has been done
    """
    type_mapping_regex = r'\[(DICT|LIST|INT|FLOAT|STR|UPPER|LOWER|REPLACE|TITLE):([\w\W]*)\]'
    type_mapping_match_group = re.match(type_mapping_regex, param)
    new_param = param
    param_transformed = False

    if type_mapping_match_group:
        param_transformed = True
        if type_mapping_match_group.group(1) in ['DICT', 'LIST']:
            try:
                new_param = json.loads(type_mapping_match_group.group(2).strip())
            except json.decoder.JSONDecodeError:
                new_param = eval(type_mapping_match_group.group(2))
        elif type_mapping_match_group.group(1) in ['INT', 'FLOAT']:
            exec(f'exec_param = {type_mapping_match_group.group(1).lower()}({type_mapping_match_group.group(2)})')
            new_param = locals()['exec_param']
        else:
            replace_param = _get_substring_replacement(type_mapping_match_group)
            new_param = new_param.replace(type_mapping_match_group.group(), replace_param)
    return new_param, param_transformed


def _get_substring_replacement(type_mapping_match_group):
    """
    Transform param value according to the specified prefix.
    Available transformations: STR, UPPER, LOWER, REPLACE, TITLE

    :param type_mapping_match_group: match group
    :return: return the string with the replaced param
    """
    if type_mapping_match_group.group(1) == 'STR':
        replace_param = type_mapping_match_group.group(2)
    elif type_mapping_match_group.group(1) == 'UPPER':
        replace_param = type_mapping_match_group.group(2).upper()
    elif type_mapping_match_group.group(1) == 'LOWER':
        replace_param = type_mapping_match_group.group(2).lower()
    elif type_mapping_match_group.group(1) == 'REPLACE':
        params_to_replace = type_mapping_match_group.group(2).split('::')
        replace_param = params_to_replace[2] if len(params_to_replace) > 2 else ''
        param_to_replace = params_to_replace[1] if params_to_replace[1] != '\\n' else '\n'
        param_to_replace = params_to_replace[1] if params_to_replace[1] != '\\r' else '\r'
        replace_param = params_to_replace[0].replace(param_to_replace, replace_param)
    elif type_mapping_match_group.group(1) == 'TITLE':
        replace_param = "".join(map(min, zip(type_mapping_match_group.group(2),
                                             type_mapping_match_group.group(2).title())))
    return replace_param


def _get_format_with_number_of_decimals(base, language):
    """
    Get the format and the number of decimals from the base string.
    """
    def _is_only_date(base):
        return 'TODAY' in base

    def _default_format(base):
        date_format = '%d/%m/%Y' if language == 'es' else '%Y/%m/%d'
        if _is_only_date(base):
            return date_format
        return f'{date_format} %H:%M:%S'

    format_matcher = re.search(r'\((.*)\)', base)
    if format_matcher and len(format_matcher.groups()) == 1:
        time_format = format_matcher.group(1)
        decimal_matcher = re.search(r'%(\d+)f', time_format)
        if decimal_matcher and len(decimal_matcher.groups()) == 1:
            return time_format.replace(decimal_matcher.group(0), '%f'), int(decimal_matcher.group(1))
        return time_format, None
    return _default_format(base), None


def _replace_param_date(param, language):
    """
    Transform param value in a date after applying the specified delta.
    E.g. [TODAY - 2 DAYS], [NOW - 10 MINUTES]
    An specific format could be defined in the case of NOW this way: NOW('THEFORMAT')
    where THEFORMAT is any valid format accepted by the python
    [datetime.strftime](https://docs.python.org/3/library/datetime.html#datetime.date.strftime) function.
    In the case of the %f placeholder, the syntax has been extended to allow setting an arbitrary number of digits
    (e.g. %3f would leave just the 3 most significant digits and truncate the rest).

    :param param: parameter value
    :param language: language to configure date format for NOW and TODAY
    :return: tuple with replaced value and boolean to know if replacement has been done
    """
    def _date_matcher():
        return re.match(r'\[(NOW(?:\((?:.*)\)|)|TODAY)(?:\s*([\+|-]\s*\d+)\s*(\w+)\s*)?\]', param)

    def _offset_datetime(amount, units):
        now = datetime.datetime.utcnow()
        if not amount or not units:
            return now
        the_amount = int(amount.replace(' ', ''))
        the_units = units.lower()
        return now + datetime.timedelta(**dict([(the_units, the_amount)]))

    matcher = _date_matcher()
    if not matcher:
        return param, False

    base, amount, units = list(matcher.groups())
    format_str, number_of_decimals = _get_format_with_number_of_decimals(base, language)
    date = _offset_datetime(amount, units)
    if number_of_decimals:
        decimals = f"{date.microsecond / 1_000_000:.{number_of_decimals}f}"[2:]
        format_str = format_str.replace("%f", decimals)
    return date.strftime(format_str), True


def _replace_param_fixed_length(param):
    """
    Generate a fixed length data element if param matches the expression [<type>_WITH_LENGTH_<length>]
    where <type> can be: STRING, INTEGER, STRING_ARRAY, INTEGER_ARRAY, JSON.
    E.g. [STRING_WITH_LENGTH_15]

    :param param: parameter value
    :return: tuple with replaced value and boolean to know if replacement has been done
    """
    string_seed = 'a'
    integer_seed = '1'
    new_param = param
    param_replaced = False
    # we allow partial replacements for STRING
    string_expression = re.compile(r'\[STRING_WITH_LENGTH_([0-9]+)\]')
    new_param = string_expression.sub(lambda x: int(x.group(1)) * 'a', param)
    if param.startswith('[') and param.endswith(']'):
        if any(x in param for x in ['STRING_ARRAY_WITH_LENGTH_', 'INTEGER_ARRAY_WITH_LENGTH_']):
            seeds = {'STRING': string_seed, 'INTEGER': int(integer_seed)}
            seed, length = param[1:-1].split('_ARRAY_WITH_LENGTH_')
            new_param = list(seeds[seed] for x in range(int(length)))
            param_replaced = True
        elif 'JSON_WITH_LENGTH_' in param:
            length = int(param[1:-1].split('JSON_WITH_LENGTH_')[1])
            new_param = dict((str(x), str(x)) for x in range(length))
            param_replaced = True
        elif any(x in param for x in ['INTEGER_WITH_LENGTH_']):
            length = param[len('[INTEGER_WITH_LENGTH_'):-1]
            new_param = int(integer_seed * int(length))
            param_replaced = True
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


def map_param(param):
    """
    Transform the given string by replacing specific patterns containing keys with their values,
    which can be obtained from the Behave context or from environment files or variables.
    See map_one_param function for a description of the available tags and replacement logic.

    :param param: string parameter
    :return: string with the applied replacements
    """
    if not isinstance(param, str):
        return param

    map_regex = r"[\[CONF:|\[LANG:|\[POE:|\[ENV:|\[BASE64:|\[TOOLIUM:|\[CONTEXT:|\[FILE:][^\[\]]*\]"
    map_expressions = re.compile(map_regex)

    mapped_param = param
    if map_expressions.split(param) == ['', '']:
        # The parameter is just one config value
        mapped_param = map_one_param(param)
    else:
        # The parameter is a combination of text and configuration parameters.
        for match in map_expressions.findall(param):
            mapped_param = mapped_param.replace(match, str(map_one_param(match)))

    if mapped_param != param:
        # Calling to map_param recursively to replace parameters that include another parameters
        mapped_param = map_param(mapped_param)

    return mapped_param


def map_one_param(param):
    """
    Analyze the pattern in the given string and find out its transformed value.
    Available tags and replacement values:

    - [CONF:xxxx] Value from the config dict in project_config global variable for the key xxxx (dot notation is used
      for keys, e.g. key_1.key_2.0.key_3)
    - [LANG:xxxx] String from the texts dict in language_terms global variable for the key xxxx, using the language
      specified in language global variable (dot notation is used for keys, e.g. button.label)
    - [POE:xxxx] Definition(s) from the POEditor terms list in poeditor_terms global variable for the term xxxx
    - [TOOLIUM:xxxx] Value from the toolium config in toolium_config global variable for the key xxxx (key format is
      section_option, e.g. Driver_type)
    - [CONTEXT:xxxx] Value from the behave context storage dict in behave_context global variable for the key xxxx, or
      value of the behave context attribute xxxx, if the former does not exist
    - [ENV:xxxx] Value of the OS environment variable xxxx
    - [FILE:xxxx] String with the content of the file in the path xxxx
    - [BASE64:xxxx] String with the base64 representation of the file content in the path xxxx

    :param param: string parameter
    :return: transformed value or the original string if no transformation could be applied
    """
    if not isinstance(param, str):
        return param

    type, key = _get_mapping_type_and_key(param)

    mapping_functions = {
        "CONF": {
            "prerequisites": project_config,
            "function": map_json_param,
            "args": [key, project_config]
        },
        "TOOLIUM": {
            "prerequisites": toolium_config,
            "function": map_toolium_param,
            "args": [key, toolium_config]
        },
        "CONTEXT": {
            "prerequisites": behave_context,
            "function": get_value_from_context,
            "args": [key, behave_context]
        },
        "LANG": {
            "prerequisites": language_terms and language,
            "function": get_message_property,
            "args": [key, language_terms, language]
        },
        "POE": {
            "prerequisites": poeditor_terms,
            "function": get_translation_by_poeditor_reference,
            "args": [key, poeditor_terms]
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
        param = mapping_functions[type]["function"](*mapping_functions[type]["args"])
    return param


def _get_mapping_type_and_key(param):
    """
    Get the type and the key of the given string parameter to be mapped to the appropriate value.

    :param param: string parameter to be parsed
    :return: a tuple with the type and the key to be mapped
    """
    types = ["CONF", "LANG", "POE", "ENV", "BASE64", "TOOLIUM", "CONTEXT", "FILE"]
    for type in types:
        match_group = re.match(r"\[%s:([^\[\]]*)\]" % type, param)
        if match_group:
            return type, match_group.group(1)
    return None, None


def map_json_param(param, config, copy=True):
    """
    Find the value of the given param using it as a key in the given dictionary. Dot notation is used,
    so for example "service.vamps.user" could be used to retrieve the email in the following config example:

    .. code-block:: json

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


def map_toolium_param(param, config):
    """
    Find the value of the given param using it as a key in the given toolium configuration.
    The param is expected to be in the form <section>_<property>, so for example "TextExecution_environment" could be
    used to retrieve the value of this toolium property (i.e. the string "QA"):
    [TestExecution]
    environment: QA

    :param param: key to be searched (e.g. "TextExecution_environment")
    :param config: toolium config object
    :return: mapped value
    """
    try:
        section = param.split("_", 1)[0]
        property_name = param.split("_", 1)[1]
    except IndexError:
        msg = f"Invalid format in Toolium config param '{param}'. Valid format: 'Section_option'."
        logger.error(msg)
        raise IndexError(msg)

    try:
        mapped_value = config.get(section, property_name)
        logger.debug(f"Mapping Toolium config param 'param' to its configured value '{mapped_value}'")
    except Exception:
        msg = f"'{param}' param not found in Toolium config file"
        logger.error(msg)
        raise Exception(msg)
    return mapped_value


def get_value_from_context(param, context):
    """
    Find the value of the given param using it as a key in the context storage dictionaries (context.storage or
    context.feature_storage) or in the context object itself. The key might be comprised of dotted tokens. In such case,
    the searched key is the first token. The rest of the tokens are considered nested properties/objects.
    So, for example, in the basic case, "last_request_result" could be used as key that would be searched into context
    storages or the context object itself. In a dotted case, "last_request.result" is searched as a "last_request" key
    in the context storages or as a property of the context object whose name is last_request. In both cases, when
    found, "result" is considered (and resolved) as a property or a key into the returned value.

    If the resolved element at one of the tokens is a list, then the next token (if present) is used as the index
    to select one of its elements in case it is a number, e.g. "list.1" returns the second element of the list "list".

    If the resolved element at one of the tokens is a list and the next token is a key=value expression, then the
    element in the list that matches the key=value expression is selected, e.g. "list.key=value" returns the element
    in the list "list" that has the value for key attribute. So, for example, if the list is:

    .. code-block:: json

        [
            {"key": "value1", "attr": "attr1"},
            {"key": "value2", "attr": "attr2"}
        ]

    then "list.key=value2" returns the second element in the list. Also does "list.'key'='value2'",
    "list.'key'=\"value2\"", "list.\"key\"='value2'" or "list.\"key\"=\"value2\"".

    There is not limit in the nested levels of dotted tokens, so a key like a.b.c.d will be tried to be resolved as:
    context.storage['a'].b.c.d or context.a.b.c.d

    :param param: key to be searched (e.g. "last_request_result" / "last_request.result")
    :param context: behave context
    :return: mapped value
    """
    parts = param.split('.')
    value = _get_initial_value_from_context(parts[0], context)
    msg = None

    for part in parts[1:]:
        # the regular case is having a key in a dict
        if isinstance(value, dict) and part in value:
            value = value[part]
        # evaluate if in an array, access is requested by index
        elif isinstance(value, list) and part.lstrip('-+').isdigit() \
                and abs(int(part)) < (len(value) + 1 if part.startswith("-") else len(value)):
            value = value[int(part)]
        # or by a key=value expression
        elif isinstance(value, list) and (element := _select_element_in_list(value, part)):
            value = element
        # look for an attribute in an object
        elif hasattr(value, part):
            value = getattr(value, part)
        else:
            # raise an exception if not possible to resolve the current part against the current value
            msg = _get_value_context_error_msg(value, part)
            logger.error(msg)
            raise ValueError(msg)
    return value


def _select_element_in_list(the_list, expression):
    """
    Select an element in the list that matches the key=value expression.

    :param the_list: list of dictionaries
    :param expression: key=value expression
    :return: the element in the list that matches the key=value expression
    """
    if not expression:
        return None
    tokens = expression.split('=')
    if len(tokens) != 2 or len(tokens[0]) == 0:
        return None

    def _trim_quotes(value):
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ['"', "'"]:
            return value[1:-1]
        return value

    key = _trim_quotes(tokens[0])
    value = _trim_quotes(tokens[1])
    for idx, item in enumerate(the_list):
        if key in item and item[key] == value:
            return the_list[idx]
    return None


def _get_value_context_error_msg(value, part):
    """
    Returns an appropriate error message when an error occurs resolving a CONTEXT reference.

    :param value: last value that has been correctly resolved
    :param part: token that is causing the error
    :return: a string with the error message
    """
    if isinstance(value, dict):
        return f"'{part}' key not found in {value} value in context"
    elif isinstance(value, list):
        if part.isdigit():
            return f"Invalid index '{part}', list size is '{len(value)}'. {part} >= {len(value)}."
        else:
            return f"the expression '{part}' was not able to select an element in the list"
    else:
        return f"'{part}' attribute not found in {type(value).__name__} class in context"


def _get_initial_value_from_context(initial_key, context):
    """
    Find the value of the given initial_key using it as a key in the context storage dictionaries (context.storage or
    context.feature_storage) or in the context object itself.

    :param initial_key: key to be searched in context
    :param context: behave context
    :return: mapped value
    """
    # If dynamic env is not initialized, the storages are initialized if needed

    context_storage = getattr(context, 'storage', {})
    run_storage = getattr(context, 'run_storage', {})
    feature_storage = getattr(context, 'feature_storage', {})

    if not isinstance(context_storage, collections.ChainMap):
        context_storage = collections.ChainMap(context_storage, run_storage, feature_storage)

    if initial_key in context_storage:
        return context_storage[initial_key]

    if hasattr(context, initial_key):
        return getattr(context, initial_key)

    msg = f"'{initial_key}' key not found in context"
    logger.error(msg)
    raise Exception(msg)


def get_message_property(param, language_terms, language_key):
    """
    Return the message for the given param, using it as a key in the list of language properties.
    Dot notation is used (e.g. "home.button.send").

    :param param: message key
    :param language_terms: dict with language terms
    :param language_key: language key
    :return: the message mapped to the given key in the given language
    """
    key_list = param.split(".")
    language_terms_aux = deepcopy(language_terms)
    try:
        for key in key_list:
            language_terms_aux = language_terms_aux[key]
        logger.debug(f"Mapping language param '{param}' to its configured value '{language_terms_aux[language_key]}'")
    except KeyError:
        msg = f"Mapping chain '{param}' not found in the language properties file"
        logger.error(msg)
        raise KeyError(msg)

    return language_terms_aux[language_key]


def get_translation_by_poeditor_reference(reference, poeditor_terms):
    """
    Return the translation(s) for the given POEditor reference from the given terms in poeditor_terms.

    :param reference: POEditor reference
    :param poeditor_terms: poeditor terms
    :return: list of strings with the translations from POEditor or string with the translation if only one was found
    """
    poeditor_config = project_config['poeditor'] if project_config and 'poeditor' in project_config else {}
    key = poeditor_config['key_field'] if 'key_field' in poeditor_config else 'reference'
    search_type = poeditor_config['search_type'] if 'search_type' in poeditor_config else 'contains'
    ignore_empty = poeditor_config['ignore_empty'] if 'ignore_empty' in poeditor_config else False
    ignored_definitions = [None, ''] if ignore_empty else [None]
    # Get POEditor prefixes and add no prefix option
    poeditor_prefixes = poeditor_config['prefixes'] if 'prefixes' in poeditor_config else []
    poeditor_prefixes.append('')
    translation = []
    for prefix in poeditor_prefixes:
        if len(reference.split(':')) > 1 and prefix != '':
            # If there are prefixes and the resource contains ':' apply prefix in the correct position
            complete_reference = '%s:%s%s' % (reference.split(':')[0], prefix, reference.split(':')[1])
        else:
            complete_reference = '%s%s' % (prefix, reference)
        if search_type == 'exact':
            translation = [term['definition'] for term in poeditor_terms
                           if complete_reference == term[key] and term['definition'] not in ignored_definitions]
        else:
            translation = [term['definition'] for term in poeditor_terms
                           if complete_reference in term[key] and term['definition'] not in ignored_definitions]
        if len(translation) > 0:
            break
    assert len(translation) > 0, 'No translations found in POEditor for reference %s' % reference
    translation = translation[0] if len(translation) == 1 else translation
    return translation


def set_base64_path(path):
    """
    Set a relative path to be used as the base for the file path specified in the BASE64 mapping pattern.

    :param path: relative path to be used as base for base64 mapping
    """
    global base_base64_path
    base_base64_path = path


def set_file_path(path):
    """
    Set a relative path to be used as the base for the file path specified in the FILE mapping pattern.

    :param path: relative path to be used as base for file mapping
    """
    global base_file_path
    base_file_path = path


def get_file(file_path):
    """
    Return the content of a file given its path. If a base path was previously set by using
    the set_file_path() function, the file path specified must be relative to that path.

    :param file_path: file path using slash as separator (e.g. "resources/files/doc.txt")
    :return: string with the file content
    """
    file_path_parts = (base_file_path + file_path).split("/")
    file_path = os.path.abspath(os.path.join(*file_path_parts))
    if not os.path.exists(file_path):
        raise Exception(f' ERROR - Cannot read file "{file_path}". Does not exist.')

    with open(file_path, 'r') as f:
        return f.read()


def convert_file_to_base64(file_path):
    """
    Return the content of a file given its path encoded in Base64. If a base path was previously set by using
    the set_file_path() function, the file path specified must be relative to that path.

    :param file_path: file path using slash as separator (e.g. "resources/files/doc.txt")
    :return: string with the file content encoded in Base64
    """
    file_path_parts = (base_base64_path + file_path).split("/")
    file_path = os.path.abspath(os.path.join(*file_path_parts))
    if not os.path.exists(file_path):
        raise Exception(f' ERROR - Cannot read file "{file_path}". Does not exist.')

    try:
        with open(file_path, "rb") as f:
            file_content = base64.b64encode(f.read()).decode()
    except Exception as e:
        raise Exception(f' ERROR - converting the "{file_path}" file to Base64...: {e}')
    return file_content


def store_key_in_storage(context, key, value):
    """
    Store values in context.storage, context.feature_storage or context.run_storage,
    using [key], [FEATURE:key] OR [RUN:key] from steps.
    context.storage is also updated with given key,value
    By default, values are stored in context.storage.

    :param key: key to store the value in proper storage
    :param value: value to store in key
    :param context: behave context
    :return:
    """
    clean_key = re.sub(r'[\[\]]', '', key)
    if ":" in clean_key:
        context_type = clean_key.split(":")[0]
        context_key = clean_key.split(":")[1]
        acccepted_context_types = ["FEATURE", "RUN"]
        assert context_type in acccepted_context_types, (f"Invalid key: {context_key}. "
                                                         f"Accepted keys: {acccepted_context_types}")
        if context_type == "RUN":
            context.run_storage[context_key] = value
        elif context_type == "FEATURE":
            context.feature_storage[context_key] = value
        # If dynamic env is not initialized linked or key exists in context.storage, the value is updated in it
        if hasattr(context.storage, context_key) or not isinstance(context.storage, collections.ChainMap):
            context.storage[context_key] = value
    else:
        context.storage[clean_key] = value
