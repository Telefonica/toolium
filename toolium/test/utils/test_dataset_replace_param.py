# -*- coding: utf-8 -*-
"""
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

import datetime
import re
from uuid import UUID

import pytest

from toolium.utils import dataset
from toolium.utils.dataset import replace_param


def test_replace_param_no_string():
    param = replace_param(1234)
    assert param == 1234


def test_replace_param_no_pattern():
    param = replace_param('my param')
    assert param == 'my param'


def test_replace_param_incomplete_pattern():
    param = replace_param('[INTEGER_WITH_LENGTH_4')
    assert param == '[INTEGER_WITH_LENGTH_4'


def test_replace_param_string_with_length():
    param = replace_param('[STRING_WITH_LENGTH_5]')
    assert param == 'aaaaa'


def test_replace_param_string_array_with_length():
    param = replace_param('[STRING_ARRAY_WITH_LENGTH_5]')
    assert param == ['a', 'a', 'a', 'a', 'a']


def test_replace_param_integer_with_length():
    param = replace_param('[INTEGER_WITH_LENGTH_4]')
    assert param == 1111


def test_replace_param_integer_array_with_length():
    param = replace_param('[INTEGER_ARRAY_WITH_LENGTH_4]')
    assert param == [1, 1, 1, 1]


def test_replace_param_float_with_length():
    param = replace_param('[FLOAT_WITH_LENGTH_4]')
    assert param == '[FLOAT_WITH_LENGTH_4]'


def test_replace_param_float_array_with_length():
    param = replace_param('[FLOAT_ARRAY_WITH_LENGTH_4]')
    assert param == '[FLOAT_ARRAY_WITH_LENGTH_4]'


def test_replace_param_json_with_length():
    param = replace_param('[JSON_WITH_LENGTH_3]')
    assert param == {'0': '0', '1': '1', '2': '2'}


def test_replace_param_incomplete_integer_with_length():
    param = replace_param('[INTEGER_WITH_LENGTH_4')
    assert param == '[INTEGER_WITH_LENGTH_4'


def test_replace_param_missing_param():
    param = replace_param('[MISSING_PARAM]')
    assert param is None


def test_replace_param_null():
    param = replace_param('[NULL]')
    assert param is None


def test_replace_param_true():
    param = replace_param('[TRUE]')
    assert param is True


def test_replace_param_false():
    param = replace_param('[FALSE]')
    assert param is False


def test_replace_param_empty():
    param = replace_param('[EMPTY]')
    assert param == ''


def test_replace_param_blank():
    param = replace_param('[B]')
    assert param == ' '


def test_replace_param_uuid():
    param = replace_param('[UUID]')
    assert UUID(param).version == 4


def test_replace_param_random():
    param = replace_param('[RANDOM]')
    assert len(param) == 8
    assert isinstance(param, str)


def test_replace_param_random_phone_number_with_type_inference():
    param = replace_param('[RANDOM_PHONE_NUMBER]')
    assert isinstance(param, int)
    assert len(str(param)) == 11


def test_replace_param_random_phone_number_without_type_inference():
    param = replace_param('[RANDOM_PHONE_NUMBER]', infer_param_type=False)
    assert isinstance(param, str)
    assert len(param) == 12
    assert param.startswith('+34')


def test_replace_param_random_phone_number_with_type_inference_forcing_str():
    param = replace_param('[STR:[RANDOM_PHONE_NUMBER]]')
    assert isinstance(param, str)
    assert len(param) == 12
    assert param.startswith('+34')


def test_replace_param_random_phone_number_for_given_locale():
    dataset.language = 'pt'
    dataset.country = 'BR'
    param = replace_param('[RANDOM_PHONE_NUMBER]', infer_param_type=False)
    assert isinstance(param, str)
    assert len(param) == 13
    assert param.startswith('+55')


def test_replace_param_timestamp_with_type_inference():
    param = replace_param('[TIMESTAMP]')
    assert isinstance(param, int)
    assert datetime.datetime.strptime(str(datetime.datetime.fromtimestamp(param)), '%Y-%m-%d %H:%M:%S')


def test_replace_param_timestamp_without_type_inference():
    param = replace_param('[TIMESTAMP]', infer_param_type=False)
    assert isinstance(param, str)
    assert len(param) == 10
    assert datetime.datetime.strptime(str(datetime.datetime.fromtimestamp(int(param))), '%Y-%m-%d %H:%M:%S')


def test_replace_param_timestamp_with_type_inference_forcing_str():
    param = replace_param('[STR:[TIMESTAMP]]')
    assert isinstance(param, str)
    assert len(param) == 10
    assert datetime.datetime.strptime(str(datetime.datetime.fromtimestamp(int(param))), '%Y-%m-%d %H:%M:%S')


def test_replace_param_datetime():
    param = replace_param('[DATETIME]')
    assert datetime.datetime.strptime(param, '%Y-%m-%d %H:%M:%S.%f')


def test_replace_param_datetime_language_ignored():
    param = replace_param('[DATETIME]', language='es')
    assert datetime.datetime.strptime(param, '%Y-%m-%d %H:%M:%S.%f')


def test_replace_param_today_spanish():
    param = replace_param('[TODAY]', language='es')
    assert param == datetime.datetime.utcnow().strftime('%d/%m/%Y')


def test_replace_param_today_not_spanish():
    param = replace_param('[TODAY]', language='en')
    assert param == datetime.datetime.utcnow().strftime('%Y/%m/%d')


def test_replace_param_today_offset():
    param = replace_param('[TODAY - 1 DAYS]', language='es')
    assert param == datetime.datetime.strftime(
        datetime.datetime.utcnow() - datetime.timedelta(days=1), '%d/%m/%Y')


def test_replace_param_now_spanish():
    param = replace_param('[NOW]', language='es')
    assert param == datetime.datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')


def test_replace_param_now_not_spanish():
    param = replace_param('[NOW]', language='it')
    assert param == datetime.datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S')


def test_replace_param_now_with_format():
    param = replace_param('[NOW(%Y-%m-%dT%H:%M:%SZ)]')
    assert param == datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def test_replace_param_now_with_format_and_decimals_limit():
    param = replace_param('[NOW(%Y-%m-%dT%H:%M:%S.%3fZ)]')
    param_till_dot = param[:param.find('.')]
    assert param_till_dot == datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    assert re.match(param_till_dot + r'\.\d{3}Z', param)


def test_replace_param_now_with_format_and_decimals_limit_beyond_microseconds():
    param = replace_param('[NOW(%Y-%m-%dT%H:%M:%S.%12fZ)]')
    param_till_dot = param[:param.find('.')]
    assert param_till_dot == datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    assert re.match(param_till_dot + r'\.\d{12}Z', param)


def test_not_replace_param_now_with_invalid_opening_parenthesis_in_format():
    param = replace_param('[NOW(%Y-%m-%dT(%H:%M:%SZ)]')
    assert param == '[NOW(%Y-%m-%dT(%H:%M:%SZ)]'


def test_not_replace_param_now_with_invalid_closing_parenthesis_in_format():
    param = replace_param('[NOW(%Y-%m-%dT)%H:%M:%SZ)]')
    assert param == '[NOW(%Y-%m-%dT)%H:%M:%SZ)]'


def test_replace_param_now_offset():
    param = replace_param('[NOW + 5 MINUTES]', language='es')
    assert param == datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(minutes=5), '%d/%m/%Y %H:%M:%S')


def test_replace_param_now_offset_with_format():
    param = replace_param('[NOW(%Y-%m-%dT%H:%M:%SZ) + 5 MINUTES]')
    assert param == datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(minutes=5), '%Y-%m-%dT%H:%M:%SZ')


def test_replace_param_today_offset_and_more():
    param = replace_param('The day [TODAY - 1 DAYS] was yesterday', language='es')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.utcnow() - datetime.timedelta(days=1), '%d/%m/%Y')
    assert param == f'The day {offset_date} was yesterday'


def test_replace_param_today_offset_and_more_not_spanish():
    param = replace_param('The day [TODAY - 1 DAYS] was yesterday', language='it')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.utcnow() - datetime.timedelta(days=1), '%Y/%m/%d')
    assert param == f'The day {offset_date} was yesterday'


def test_replace_param_now_offset_and_more():
    param = replace_param('I will arrive at [NOW + 10 MINUTES] tomorrow', language='es')
    offset_datetime = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(minutes=10), '%d/%m/%Y %H:%M:%S')
    assert param == f'I will arrive at {offset_datetime} tomorrow'


def test_replace_param_now_offset_and_more_not_spanish():
    param = replace_param('I will arrive at [NOW + 10 MINUTES] tomorrow', language='it')
    offset_datetime = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(minutes=10), '%Y/%m/%d %H:%M:%S')
    assert param == f'I will arrive at {offset_datetime} tomorrow'


def test_replace_param_now_offset_with_format_and_more():
    param = replace_param('I will arrive at [NOW(%Y-%m-%dT%H:%M:%SZ) + 10 MINUTES] tomorrow')
    offset_datetime = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(minutes=10), '%Y-%m-%dT%H:%M:%SZ')
    assert param == f'I will arrive at {offset_datetime} tomorrow'


def test_replace_param_now_offset_with_format_and_more_language_is_irrelevant():
    param = replace_param('I will arrive at [NOW(%Y-%m-%dT%H:%M:%SZ) + 10 MINUTES] tomorrow', language='ru')
    offset_datetime = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(minutes=10), '%Y-%m-%dT%H:%M:%SZ')
    assert param == f'I will arrive at {offset_datetime} tomorrow'


def test_replace_param_today_offset_with_format_and_more_with_extra_spaces():
    param = replace_param('The date [NOW(%Y-%m-%dT%H:%M:%SZ)   - 1    DAYS ] was yesterday')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.utcnow() - datetime.timedelta(days=1), '%Y-%m-%dT%H:%M:%SZ')
    assert param == f'The date {offset_date} was yesterday'


def test_replace_param_today_offset_and_more_with_extra_spaces():
    param = replace_param('The day [TODAY    - 1    DAYS ] was yesterday', language='es')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.utcnow() - datetime.timedelta(days=1), '%d/%m/%Y')
    assert param == f'The day {offset_date} was yesterday'


def test_replace_param_today_offset_and_more_at_the_end():
    param = replace_param('Yesterday was [TODAY - 1 DAYS]', language='es')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.utcnow() - datetime.timedelta(days=1), '%d/%m/%Y')
    assert param == f'Yesterday was {offset_date}'


def test_replace_param_today_offset_and_more_at_the_beginning():
    param = replace_param('[TODAY - 1 DAYS] is yesterday', language='es')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.utcnow() - datetime.timedelta(days=1), '%d/%m/%Y')
    assert param == f'{offset_date} is yesterday'


def test_replace_param_today_offsets_and_more():
    param = replace_param(
        'The day [TODAY - 1 DAYS] was yesterday and I have an appointment at [NOW + 10 MINUTES]', language='es')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.utcnow() - datetime.timedelta(days=1), '%d/%m/%Y')
    offset_datetime = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(minutes=10), '%d/%m/%Y %H:%M:%S')
    assert param == f'The day {offset_date} was yesterday and I have an appointment at {offset_datetime}'


def test_replace_param_now_offsets_with_format_and_more():
    param = replace_param(
        'The date [NOW(%Y-%m-%dT%H:%M:%SZ) - 1 DAYS] was yesterday '
        'and I have an appointment at [NOW(%Y-%m-%dT%H:%M:%SZ) + 10 MINUTES]')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.utcnow() - datetime.timedelta(days=1), '%Y-%m-%dT%H:%M:%SZ')
    offset_datetime = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(minutes=10), '%Y-%m-%dT%H:%M:%SZ')
    assert param == f'The date {offset_date} was yesterday and I have an appointment at {offset_datetime}'


def test_replace_param_now_offsets_with_and_without_format_and_more():
    param = replace_param(
        'The date [NOW(%Y-%m-%dT%H:%M:%SZ) - 1 DAYS] was yesterday '
        'and I have an appointment at [NOW + 10 MINUTES]', language='es')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.utcnow() - datetime.timedelta(days=1), '%Y-%m-%dT%H:%M:%SZ')
    offset_datetime = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(minutes=10), '%d/%m/%Y %H:%M:%S')
    assert param == f'The date {offset_date} was yesterday and I have an appointment at {offset_datetime}'


@pytest.mark.parametrize('in_param, number_of_digits_in_fractional_part, out_param',
                         [['7.5', '2', 7.5],
                          ['3.33333333', '3', 3.333],
                          ['123', '5', 123.0],
                          ['0.001', '2', 0.0],
                          ['0.4', '0', 0],
                          ['0.6', '0', 1]
                          ])
def test_replace_param_round_with_type_inference(in_param, number_of_digits_in_fractional_part, out_param):
    param = replace_param(f'[ROUND:{in_param}::{number_of_digits_in_fractional_part}]')
    assert param == out_param


@pytest.mark.parametrize('in_param, number_of_digits_in_fractional_part, out_param',
                         [['7.5', '2', '7.50'],
                          ['3.33333333', '3', '3.333'],
                          ['123', '5', '123.00000'],
                          ['0.001', '2', '0.00'],
                          ['0.4', '0', '0'],
                          ['0.6', '0', '1']
                          ])
def test_replace_param_round_without_type_inference(in_param, number_of_digits_in_fractional_part, out_param):
    param = replace_param(f'[ROUND:{in_param}::{number_of_digits_in_fractional_part}]', infer_param_type=False)
    assert param == out_param


def test_replace_param_str_int():
    param = replace_param('[STR:28]')
    assert isinstance(param, str)
    assert param == '28'


def test_replace_param_str():
    param = replace_param('[STR:abc]')
    assert isinstance(param, str)
    assert param == 'abc'


def test_replace_param_int():
    param = replace_param('[INT:28]')
    assert isinstance(param, int)
    assert param == 28


def test_replace_param_float():
    param = replace_param('[FLOAT:28]')
    assert isinstance(param, float)
    assert param == 28.0


def test_replace_param_list_integers():
    param = replace_param('[LIST:[1,2,3]]')
    assert isinstance(param, list)
    assert param == [1, 2, 3]


def test_replace_param_list_strings():
    param = replace_param("[LIST:['1','2','3']]")
    assert isinstance(param, list)
    assert param == ['1', '2', '3']


def test_replace_param_list_json_format():
    param = replace_param('[LIST:["value", true, null]]')
    assert param == ["value", True, None]


def test_replace_param_dict():
    param = replace_param("[DICT:{'a':'test1','b':'test2','c':'test3'}]")
    assert isinstance(param, dict)
    assert param == {'a': 'test1', 'b': 'test2', 'c': 'test3'}


def test_replace_param_dict_json_format():
    param = replace_param('[DICT:{"key": "value", "key_2": true, "key_3": null}]')
    assert param == {"key": "value", "key_2": True, "key_3": None}


def test_replace_param_upper():
    param = replace_param('[UPPER:test]')
    assert param == 'TEST'
    param = replace_param('[UPPER:TeSt]')
    assert param == 'TEST'


def test_replace_param_lower():
    param = replace_param('[LOWER:TEST]')
    assert param == 'test'
    param = replace_param('[LOWER:TeSt]')
    assert param == 'test'


def test_replace_param_type_inference():
    param = replace_param('1234')  # int
    assert param == 1234
    param = replace_param('0.5')  # float
    assert param == 0.5
    param = replace_param('True')  # boolean
    assert param is True
    param = replace_param('None')  # None
    assert param is None
    param = replace_param("{'a':'test1', 'b':True, 'c':None}")  # dict
    assert param == {'a': 'test1', 'b': True, 'c': None}
    param = replace_param("['1', True,None]")  # list
    assert param == ['1', True, None]
    param = replace_param('{"a":"test1", "b":true, "c":null}')  # JSON object
    assert param == {'a': 'test1', 'b': True, 'c': None}
    param = replace_param('["1", true, null]')  # JSON list
    assert param == ['1', True, None]
    param = replace_param('true')  # JSON boolean
    assert param == 'true'
    param = replace_param('null')  # JSON null
    assert param == 'null'


def test_replace_param_type_inference_disabled():
    param = replace_param('1234', infer_param_type=False)
    assert param == '1234'
    param = replace_param('0.5', infer_param_type=False)
    assert param == '0.5'
    param = replace_param('True', infer_param_type=False)
    assert param == 'True'
    param = replace_param('None', infer_param_type=False)
    assert param == 'None'
    param = replace_param("{'a':'test1', 'b':True, 'c':None}", infer_param_type=False)
    assert param == "{'a':'test1', 'b':True, 'c':None}"
    param = replace_param("['1', True, None]", infer_param_type=False)
    assert param == "['1', True, None]"
    param = replace_param('{"a":"test1", "b":true, "c":null}', infer_param_type=False)
    assert param == '{"a":"test1", "b":true, "c":null}'
    param = replace_param('["1", true, null]', infer_param_type=False)
    assert param == '["1", true, null]'


def test_replace_param_partial_string_with_length():
    param = replace_param('parameter=[STRING_WITH_LENGTH_5]')
    assert param == 'parameter=aaaaa'
    param = replace_param('[STRING_WITH_LENGTH_5] is string')
    assert param == 'aaaaa is string'
    param = replace_param('parameter [STRING_WITH_LENGTH_5] is string')
    assert param == 'parameter aaaaa is string'


def test_replace_param_replace():
    param = replace_param('[REPLACE:https://url.com::https::http]')
    assert param == "http://url.com"
    param = replace_param('[REPLACE:https://url.com::https://]')
    assert param == "url.com"


def test_replace_param_title():
    param = replace_param('[TITLE:hola hola]')
    assert param == "Hola Hola"
    param = replace_param('[TITLE:holahola]')
    assert param == "Holahola"
    param = replace_param('[TITLE:hOlA]')
    assert param == "HOlA"
