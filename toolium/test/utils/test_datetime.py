# -*- coding: utf-8 -*-
u"""
Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U.
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

from toolium.utils.datetime_utils import time_str_to_secs, secs_to_time_str, secs_to_duration_string


def test_time_to_secs_with_ms_zero_fill():
    seconds = time_str_to_secs(u'01:23:45.678')

    assert seconds == 5025.678


def test_time_to_secs_with_ms_no_zero_fill():
    seconds = time_str_to_secs(u'1:23:45.678')

    assert seconds == 5025.678


def test_time_to_secs_with_hour_gtr_12():
    seconds = time_str_to_secs(u'98:12:54.321')

    assert seconds == 353574.321


def test_time_to_secs_with_short_ms():
    seconds = time_str_to_secs(u'01:23:45.6')

    assert seconds == 5025.6


def test_time_to_secs_without_ms():
    seconds = time_str_to_secs(u'1:23:45*')

    assert seconds == 5025.0


def test_time_to_secs_without_secs():
    seconds = time_str_to_secs(u'1:23')

    assert seconds == 4980.0


def test_fixed_time_to_secs_days():
    seconds = time_str_to_secs(u'2d')

    assert seconds == 172800.0


def test_fixed_time_to_secs_days_long_singular():
    seconds = time_str_to_secs(u'1 days')

    assert seconds == 86400.0


def test_fixed_time_to_secs_hours():
    seconds = time_str_to_secs(u'3h')

    assert seconds == 10800.0


def test_fixed_time_to_secs_hours_long_spaced():
    seconds = time_str_to_secs(u'3 hours')

    assert seconds == 10800.0


def test_fixed_time_to_secs_minutes_spaced():
    seconds = time_str_to_secs(u'50 mi')

    assert seconds == 3000.0


def test_fixed_time_to_secs_minutes_long():
    seconds = time_str_to_secs(u'50minutes')

    assert seconds == 3000.0


def test_fixed_time_to_secs_seconds():
    seconds = time_str_to_secs(u'3600s')

    assert seconds == 3600.0


def test_fixed_time_to_secs_seconds_long():
    seconds = time_str_to_secs(u'3600s')

    assert seconds == 3600.0


def test_fixed_time_to_secs_milliseconds():
    seconds = time_str_to_secs(u'500000ms')

    assert seconds == 500.0


def test_fixed_time_to_secs_milliseconds_long_spaced():
    seconds = time_str_to_secs(u'500000 milliseconds')

    assert seconds == 500.0


def test_fixed_time_to_secs_no_symbol():
    seconds = time_str_to_secs(u'20000')

    assert seconds == 20000.0


def test_fixed_time_to_secs_no_symbol_decimal():
    seconds = time_str_to_secs(u'20000.678')

    assert seconds == 20000.678


def test_seconds_to_time_str():
    time_str = secs_to_time_str(5025.678)

    assert u'01:23:45.678' == time_str


def test_seconds_to_time_with_hour_gtr_12():
    time_str = secs_to_time_str(353574.321)

    assert time_str == u'98:12:54.321'


def test_seconds_to_duration_str():
    time_str = secs_to_duration_string(5025.678)

    assert u'1 hour, 23 minutes, 45 seconds, 678.0 milliseconds' == time_str


def test_seconds_to_duration_str_with_hour_gtr_12():
    time_str = secs_to_duration_string(353574.321)

    assert time_str == u'4 days, 2 hours, 12 minutes, 54 seconds, 321.0 milliseconds'


def test_seconds_to_duration_str_only_seconds():
    time_str = secs_to_duration_string(35)

    assert u'35 seconds' == time_str


def test_seconds_to_duration_only_milliseconds():
    time_str = secs_to_duration_string(.678)

    assert u'678.0 milliseconds' == time_str


def test_seconds_to_duration_str_one_day():
    time_str = secs_to_duration_string(86400)

    assert u'1 day' == time_str
