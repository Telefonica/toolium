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

import logging
import phonenumbers
import random
import re
import uuid

from faker import Faker

__logger__ = logging.getLogger(__name__)


class DataGenerator(object):
    """
    Class to generate fake data for testing.
    Supported data: street_address, email, phone_number, postal_code.
    """

    def __init__(self):
        self._provider = DataGenerator.get_locale()
        self._fake = Faker(self._provider)

    @property
    def street_address(self):
        """
        Generate random street address: street/avenue/road, street number, floor/door...
        """
        return self._fake.street_address()

    @property
    def locality(self):
        """
        Generate random locality. Now return only cities
        """
        return self._fake.city()

    @property
    def region(self):
        """
        Generate random region of the country
        """
        return self._fake.region()

    @property
    def email(self):
        """
        Generate random email.
        """
        return self._fake.email()

    @property
    def phone_number(self):
        """
        Generate random phone_number for a country in international format.
        For example: '+448081570270'
        If locale is not defined, return phone number from anywhere.
        """
        if self._provider:  # Example: en_GB
            region_code = self._provider.split('_')[-1]
            raw_phone_number = phonenumbers.parse(self._fake.phone_number(), region_code)
            return phonenumbers.format_number(raw_phone_number, phonenumbers.PhoneNumberFormat.E164)
        return self._fake.phone_number()

    @property
    def postal_code(self):
        """
        Generate a random country postal code.
        """
        while True:
            postal_code = self._fake.postcode()
            if DataGenerator.is_valid_postcode(self._provider, postal_code):
                return postal_code

    @property
    def country_code(self):
        """
        Generate a country code in iso3166-1 alpha-2 format.
        """
        return self._fake.country_code()

    @property
    def random_uuidv4(self) -> str:
        """
        Generate a random uuid v4 string
        """
        return str(uuid.uuid4())

    @staticmethod
    def random_int(length):
        return ''.join(["{}".format(random.randint(0, 9)) for _ in range(0, int(length))])

    @staticmethod
    def get_locale():
        """
        Return the locale.
        If language and country properties are not defined, 'es_ES' is set.
        """
        from toolium.utils.dataset import language, country
        locale = 'es_ES'
        if language and ('-' in language or '_' in language):
            # When language contain the complete locale value
            locale = language.replace('-', '_')
            locale = f"{locale.split('_')[0]}_{locale.split('_')[1].upper()}"
        elif language and country:
            locale = f'{language}_{country.upper()}'
        return locale

    @staticmethod
    def is_valid_postcode(provider, postal_code):
        """
        Validate postal codes by locale.
        Can be added custom validations for the country.
        """
        if provider == 'es_ES':
            return re.match(r"(?:0[1-9]|[1-4]\d|5[0-2])\d{3}$", postal_code)
        return True
