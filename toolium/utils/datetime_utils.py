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

import re

TIME_PATTERN = re.compile(u'([0-9]+):([0-5][0-9])(:([0-5][0-9]))?(.([0-9]{1,3}))?')
FIXED_TIME_PATTERN = re.compile(
    u'([0-9\\.]+) ?(ms|millisecond(s?)|s|second(s?)|mi|minute(s?)|h|hour(s?)|d|day(s?)|w|week(s?)|m|month(s?)|y|year(s?))?')


def time_str_to_secs(time_str):
    """
    Convert a time string to seconds with decimals.
     * **01:23:45.678** => 5025.678
     * **12:34:56.789** => 45296.789
     * **1:23:45.678** => 5025.678
     * **1:23:45** => 5025.0
     * **1:23** => 4980.0
     * **2d** => 172800.0
     * **3h** => 10800.0
     * **50mi** => 3000.0
     * **3600s** => 3600.0
     * **500000ms** => 500.0
     * **20000** => 20000.0
    :param time_str: Time string to parse.
    :return: Time converted to seconds.
    """

    def parse_time():
        """
        Parse a time string with time format (hh:mm:ss.SSS)
        :return: Time converted to seconds.
        """
        hours = float(time_matcher.group(1))
        minutes = hours * 60 + float(time_matcher.group(2))
        seconds = minutes * 60 + float(time_matcher.group(4) if time_matcher.group(4) else 0)
        milliseconds_aux = u'{num:<03}'.format(num=time_matcher.group(6) if time_matcher.group(6) else '0')

        milliseconds = seconds * 1000 + float(milliseconds_aux)

        return milliseconds / 1000

    def parse_fixed_time():
        """
        Parse a time string with fixed unit format.
        :return: Time converted to seconds.
        """
        time = float(fixed_time_matcher.group(1))
        time_type = fixed_time_matcher.group(2)

        if time_type in [u'ms', u'millisecond', u'milliseconds']:
            return time / 1000
        elif time_type in [None, u's', u'second', u'seconds']:
            return time
        elif time_type in [u'mi', u'minute', u'minutes']:
            return time * 60
        elif time_type in [u'h', u'hour', u'hours']:
            return time * 60 * 60
        elif time_type in [u'd', u'day', u'days']:
            return time * 60 * 60 * 24
        elif time_type in [u'w', u'week', u'weeks']:
            return time * 60 * 60 * 24 * 7
        elif time_type in [u'm', u'month', u'months']:
            return time * 60 * 60 * 24 * 30
        elif time_type in [u'y', u'year', u'years']:
            return time * 60 * 60 * 24 * 365

    time_matcher = TIME_PATTERN.match(time_str)
    fixed_time_matcher = FIXED_TIME_PATTERN.match(time_str)

    if time_matcher:
        return parse_time()
    elif fixed_time_matcher:
        return parse_fixed_time()
    else:
        return u'Unsupported time string: {time_str}'.format(time_str=time_str)


def secs_to_time_str(time):
    """
    Convert seconds to time string (hh:mm:ss.SSS)
    :param time: Seconds
    :return: Time string
    """
    aux_time = time * 1000
    # Milliseconds
    aux_time, milliseconds = divmod(aux_time, 1000)
    # Seconds
    aux_time, seconds = divmod(int(aux_time), 60)
    # Minutes
    aux_time, minutes = divmod(int(aux_time), 60)
    # Hours
    hours = aux_time

    return u'{h:02d}:{m:02d}:{s:02d}.{ms:03d}' \
        .format(h=int(hours), m=int(minutes), s=int(seconds), ms=int(milliseconds))


def secs_to_duration_string(time):
    """
    Convert seconds to time long string. Each time type is specified if is not zero. the maximum type is days.
    TODO: Add support weeks, months, years.
    :param time: Seconds
    :return: Time long string
    """

    def parse_time_unit(time_unit, time_type_singular, time_type_plural=None):
        """
        Parse the specified time unit to it time long string. Appends a coma if is necessary.
        :param time_unit: Amount of time for specified type.
        :param time_type_singular: Singular name for current time type.
        :param time_type_plural: Plural name for current time type. If is ``None``, an *s* is appended to singular name.
        :return: time long string for current time type.
        """
        prefix = u'' if duration_str == u'' else u', '

        if time_unit == 1:
            time_type = time_type_singular
        elif not time_type_plural:
            time_type = time_type_singular + u's'
        else:
            time_type = time_type_plural

        return u'{prefix}{time_unit} {time_type}'.format(prefix=prefix, time_unit=time_unit, time_type=time_type)

    aux_time = time * 1000
    # Milliseconds
    aux_time, milliseconds = divmod(aux_time, 1000)
    # Seconds
    aux_time, seconds = divmod(int(aux_time), 60)
    # Minutes
    aux_time, minutes = divmod(int(aux_time), 60)
    # Hours
    aux_time, hours = divmod(int(aux_time), 24)
    # Days
    days = aux_time

    duration_str = u''

    if days:
        duration_str += parse_time_unit(days, u'day')
    if hours:
        duration_str += parse_time_unit(hours, u'hour')
    if minutes:
        duration_str += parse_time_unit(minutes, u'minute')
    if seconds:
        duration_str += parse_time_unit(seconds, u'second')
    if milliseconds:
        duration_str += parse_time_unit(milliseconds, u'millisecond')

    return duration_str
