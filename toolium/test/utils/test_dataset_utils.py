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
    param = replace_param("{'a':'test1', 'b':True, 'c':None}")  # dict
    assert param == {'a': 'test1', 'b': True, 'c': None}
    param = replace_param("['1', True,None]")  # list
    assert param == ['1', True, None]
    param = replace_param('{"a":"test1", "b":true, "c":null}')  # JSON object
    assert param == {'a': 'test1', 'b': True, 'c': None}
    param = replace_param('["1", true, null]')  # JSON list
    assert param == ['1', True, None]


def test_replace_param_type_inference_disabled():
    param = replace_param('1234', infer_param_type=False)
    assert param == '1234'
    param = replace_param('0.5', infer_param_type=False)
    assert param == '0.5'
    param = replace_param("{'a':'test1', 'b':True, 'c':None}", infer_param_type=False)
    assert param == "{'a':'test1', 'b':True, 'c':None}"
    param = replace_param("['1', True, None]", infer_param_type=False)
    assert param == "['1', True, None]"
    param = replace_param('{"a":"test1", "b":true, "c":null}', infer_param_type=False)
    assert param == '{"a":"test1", "b":true, "c":null}'
    param = replace_param('["1", true, null]', infer_param_type=False)
    assert param == '["1", true, null]'
