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

from six import string_types
from six.moves import xrange

logger = logging.getLogger(__name__)


def replace_param(param, language='es'):
    """
    Available replacements:
        [STRING_WITH_LENGTH_XX] Generates a fixed length string
        [INTEGER_WITH_LENGTH_XX] Generates a fixed length integer
        [STRING_ARRAY_WITH_LENGTH_XX] Generates a fixed length array of strings
        [INTEGER_ARRAY_WITH_LENGTH_XX] Generates a fixed length array of integers
        [JSON_WITH_LENGTH_XX] Generates a fixed length JSON
        [MISSING_PARAM] Remove the param from the Dataset
        [EMPTY] Empty string
        [B] Add Blank space
        [RANDOM] Generate random value
        [DATETIME] Add a timestamp
        [NOW] Similar to DATETIME without milliseconds
        [NOW + 2 DAYS] Similar to NOW but two days later
        [NOW - 1 MINUTES] Similar to NOW but one minute earlier
        [TODAY] Similar to NOW without time
        [TODAY + 2 DAYS] Functionality similar to NOW, but only with date offsets (days, weeks)
    :param param: parameter value
    :param language: language to configure date format for NOW and TODAY
    :return: data with the correct replacements
    """
    if not isinstance(param, string_types):
        return param

    new_param, is_replaced = _replace_param_type(param)
    if not is_replaced:
        new_param, is_replaced = _replace_param_replacement(param, language)
    if not is_replaced:
        new_param, is_replaced = _replace_param_transform_string(param)
    if not is_replaced:
        new_param, is_replaced = _replace_param_date(param, language)
    if not is_replaced:
        new_param, is_replaced = _replace_param_fixed_length(param)

    if is_replaced:
        logger.debug('Replaced param from "%s" to "%s"' % (param, new_param))
        return new_param
    else:
        return param


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
    new_param = None
    is_replaced = False
    for key in param_types.keys():
        if key in param:
            new_param = param_types[key]
            is_replaced = True
            break
    return new_param, is_replaced


def _replace_param_replacement(param, language):
    """Replace partial param value

    :param param: parameter value
    :param language: language to configure date format for NOW and TODAY
    :return: tuple with replaced value and boolean to know if replacement has been done
    """
    date_format = '%d/%m/%Y %H:%M:%S' if language == 'es' else '%Y/%m/%d %H:%M:%S'
    date_day_format = '%d/%m/%Y' if language == 'es' else '%Y/%m/%d'
    replacements = {
        '[EMPTY]': '',
        '[B]': ' ',
        '[RANDOM]': uuid.uuid4().hex[0:8],
        '[DATETIME]': str(datetime.datetime.utcnow()),
        '[NOW]': str(datetime.datetime.utcnow().strftime(date_format)),
        '[TODAY]': str(datetime.datetime.utcnow().strftime(date_day_format))
    }
    new_param = None
    is_replaced = False
    for key in replacements.keys():
        if key in param:
            new_param = param.replace(key, replacements[key])
            is_replaced = True
            break
    return new_param, is_replaced


def _replace_param_transform_string(param):
    """Transform param value

    :param param: parameter value
    :return: tuple with replaced value and boolean to know if replacement has been done
    """
    type_mapping_regex = r'\[(DICT|LIST|INT|FLOAT|STR|UPPER|LOWER):(.*)\]'
    type_mapping_match_group = re.match(type_mapping_regex, param)
    new_param = None
    is_replaced = False

    if type_mapping_match_group:
        is_replaced = True
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
    return new_param, is_replaced


def _replace_param_date(param, language):
    """Transform param value in a date

    :param param: parameter value
    :param language: language to configure date format for NOW and TODAY
    :return: tuple with replaced value and boolean to know if replacement has been done
    """
    date_format = '%d/%m/%Y %H:%M:%S' if language == 'es' else '%Y/%m/%d %H:%M:%S'
    date_day_format = '%d/%m/%Y' if language == 'es' else '%Y/%m/%d'
    date_matcher = re.match(r'\[(NOW|TODAY)\s*([\+|-]\s*\d+)\s*(\w+)\s*\]', param)
    new_param = None
    is_replaced = False

    if date_matcher and len(date_matcher.groups()) == 3:
        configuration = dict([(date_matcher.group(3).lower(), int(date_matcher.group(2).replace(' ', '')))])
        now = (date_matcher.group(1) == 'NOW')
        reference_date = datetime.datetime.utcnow() if now else datetime.datetime.utcnow().date()
        replace_value = reference_date + datetime.timedelta(**configuration)
        new_param = replace_value.strftime(date_format) if now else replace_value.strftime(date_day_format)
        is_replaced = True
    return new_param, is_replaced


def _replace_param_fixed_length(param):
    """Generate a fixed length param if the elements matches the expected expression

    :param param: parameter value
    :return: tuple with replaced value and boolean to know if replacement has been done
    """
    new_param = None
    is_replaced = False
    if param.startswith('[') and param.endswith(']'):
        if any(x in param for x in ['STRING_ARRAY_WITH_LENGTH_', 'INTEGER_ARRAY_WITH_LENGTH_']):
            seeds = {'STRING': 'a', 'INTEGER': 1}
            seed, length = param[1:-1].split('_ARRAY_WITH_LENGTH_')
            new_param = list(seeds[seed] for x in xrange(int(length)))
            is_replaced = True
        elif 'JSON_WITH_LENGTH_' in param:
            length = int(param[1:-1].split('JSON_WITH_LENGTH_')[1])
            new_param = dict((str(x), str(x)) for x in xrange(length))
            is_replaced = True
        elif any(x in param for x in ['STRING_WITH_LENGTH_', 'INTEGER_WITH_LENGTH_']):
            seeds = {'STRING': 'a', 'INTEGER': '1'}
            # The chain to be generated can be just a part of param
            start = param.find('[')
            end = param.find(']')
            seed, length = param[start + 1:end].split('_WITH_LENGTH_')
            generated_part = seeds[seed] * int(length)
            placeholder = '[' + seed + '_WITH_LENGTH_' + length + ']'
            new_param = param.replace(placeholder, generated_part)
            is_replaced = True
            if seed == 'INTEGER':
                new_param = int(new_param)
    return new_param, is_replaced


def generate_fixed_length_param(param):
    """Generate a fixed length param if the elements matches the expression
    [<type>_WITH_LENGTH_<length>] where <type> can be:
    STRING, INTEGER, STRING_ARRAY, INTEGER_ARRAY, JSON.
    E.g.: [STRING_WITH_LENGTH_15]

    :param param: parameter value
    :return: replaced value
    """
    new_param, is_replaced = _replace_param_fixed_length(param)
    if is_replaced:
        return new_param
    else:
        return param
