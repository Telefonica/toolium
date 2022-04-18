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


def test_replace_param_random():
    param = replace_param('[RANDOM]')
    assert len(param) == 8
    assert type(param) == str


def test_replace_param_random_phone_number_with_type_inference():
    param = replace_param('[RANDOM_PHONE_NUMBER]')
    assert type(param) == int
    assert len(str(param)) == 11


def test_replace_param_random_phone_number_without_type_inference():
    param = replace_param('[RANDOM_PHONE_NUMBER]', infer_param_type=False)
    assert type(param) == str
    assert len(param) == 12
    assert param.startswith('+34654')


def test_replace_param_random_phone_number_with_type_inference_forcing_str():
    param = replace_param('[STR:[RANDOM_PHONE_NUMBER]]')
    assert type(param) == str
    assert len(param) == 12
    assert param.startswith('+34654')


def test_replace_param_timestamp_with_type_inference():
    param = replace_param('[TIMESTAMP]')
    assert type(param) == int
    assert datetime.datetime.strptime(str(datetime.datetime.fromtimestamp(param)), '%Y-%m-%d %H:%M:%S')


def test_replace_param_timestamp_without_type_inference():
    param = replace_param('[TIMESTAMP]', infer_param_type=False)
    assert type(param) == str
    assert len(param) == 10
    assert datetime.datetime.strptime(str(datetime.datetime.fromtimestamp(int(param))), '%Y-%m-%d %H:%M:%S')


def test_replace_param_timestamp_with_type_inference_forcing_str():
    param = replace_param('[STR:[TIMESTAMP]]')
    assert type(param) == str
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
    assert param == datetime.datetime.today().strftime('%d/%m/%Y')


def test_replace_param_today_not_spanish():
    param = replace_param('[TODAY]', language='en')
    assert param == datetime.datetime.today().strftime('%Y/%m/%d')


def test_replace_param_today_offset():
    param = replace_param('[TODAY - 1 DAYS]', language='es')
    assert param == datetime.datetime.strftime(
        datetime.datetime.today() - datetime.timedelta(days=1), '%d/%m/%Y')


def test_replace_param_now_spanish():
    param = replace_param('[NOW]', language='es')
    assert param == datetime.datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')


def test_replace_param_now_not_spanish():
    param = replace_param('[NOW]', language='it')
    assert param == datetime.datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S')


def test_replace_param_now_offset():
    param = replace_param('[NOW + 5 MINUTES]', language='es')
    assert param == datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(minutes=5), '%d/%m/%Y %H:%M:%S')
    
    
def test_replace_param_today_offset_and_more():
    param = replace_param('The day [TODAY - 1 DAYS] was yesterday', language='es')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.today() - datetime.timedelta(days=1), '%d/%m/%Y')
    assert param == f'The day {offset_date} was yesterday'
    
    
def test_replace_param_today_offset_and_more_not_spanish():
    param = replace_param('The day [TODAY - 1 DAYS] was yesterday', language='it')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.today() - datetime.timedelta(days=1), '%Y/%m/%d')
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


def test_replace_param_today_offset_and_more_with_extra_spaces():
    param = replace_param('The day [TODAY    - 1    DAYS ] was yesterday', language='es')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.today() - datetime.timedelta(days=1), '%d/%m/%Y')
    assert param == f'The day {offset_date} was yesterday'
    

def test_replace_param_today_offset_and_more_at_the_end():
    param = replace_param('Yesterday was [TODAY - 1 DAYS]', language='es')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.today() - datetime.timedelta(days=1), '%d/%m/%Y')
    assert param == f'Yesterday was {offset_date}'
    

def test_replace_param_today_offset_and_more_at_the_beginning():
    param = replace_param('[TODAY - 1 DAYS] is yesterday', language='es')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.today() - datetime.timedelta(days=1), '%d/%m/%Y')
    assert param == f'{offset_date} is yesterday'


def test_replace_param_today_offsets_and_more():
    param = replace_param('The day [TODAY - 1 DAYS] was yesterday and I have an appointment at [NOW + 10 MINUTES]', language='es')
    offset_date = datetime.datetime.strftime(
        datetime.datetime.today() - datetime.timedelta(days=1), '%d/%m/%Y')
    offset_datetime = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(minutes=10), '%d/%m/%Y %H:%M:%S')
    assert param == f'The day {offset_date} was yesterday and I have an appointment at {offset_datetime}'


def test_replace_param_str_int():
    param = replace_param('[STR:28]')
    assert type(param) == str
    assert param == '28'


def test_replace_param_str():
    param = replace_param('[STR:abc]')
    assert type(param) == str
    assert param == 'abc'


def test_replace_param_int():
    param = replace_param('[INT:28]')
    assert type(param) == int
    assert param == 28


def test_replace_param_float():
    param = replace_param('[FLOAT:28]')
    assert type(param) == float
    assert param == 28.0


def test_replace_param_list_integers():
    param = replace_param('[LIST:[1,2,3]]')
    assert type(param) == list
    assert param == [1, 2, 3]


def test_replace_param_list_strings():
    param = replace_param("[LIST:['1','2','3']]")
    assert type(param) == list
    assert param == ['1', '2', '3']


def test_replace_param_dict():
    param = replace_param("[DICT:{'a':'test1','b':'test2','c':'test3'}]")
    assert type(param) == dict
    assert param == {'a': 'test1', 'b': 'test2', 'c': 'test3'}


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
