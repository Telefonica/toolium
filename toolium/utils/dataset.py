# -*- coding: utf-8 -*-
u"""
Copyright 2021 Telefónica Investigación y Desarrollo, S.A.U.
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

import uuid
import re
import datetime
import logging
import random
import string
from ast import literal_eval

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
    this function also tries to infer and cast the result to the most appropriate data type.
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
            logger.debug('Replaced param from "%s" to "%s"' % (param, new_param))
        else:
            logger.debug('Replaced param from "%s" to %s' % (param, new_param))
    return new_param


def _replace_param_type(param):
    """Replace param to a new param type

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
    """Replace partial param value.
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
        '[RANDOM]': ''.join([random.choice(string.ascii_lowercase), *(random.choice(alphanums) for i in range(7))]),
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
    """Transform param value according to the specified prefix
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
            exec(u'exec_param = {type}({value})'.format(type=type_mapping_match_group.group(1).lower(),
                                                        value=type_mapping_match_group.group(2)))
            new_param = locals()['exec_param']
        elif type_mapping_match_group.group(1) == 'UPPER':
            new_param = type_mapping_match_group.group(2).upper()
        elif type_mapping_match_group.group(1) == 'LOWER':
            new_param = type_mapping_match_group.group(2).lower()
    return new_param, param_transformed


def _replace_param_date(param, language):
    """Transform param value in a date after applying the specified delta
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
    """Generate a fixed length data element if param matches the expression [<type>_WITH_LENGTH_<length>]
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
    Transform the param from string to the inferred data type
    E.g. '1234' -> 1234, '0.50' -> 0.5, ["a", "b"]' -> ["a", "b"], '{"a": "b"}' -> {"a": "b"}

    :param param: data to be transformed
    :return data with the inferred type
    """
    new_param = param
    try:
        new_param = literal_eval(param)
    except Exception:
        pass
    return new_param
