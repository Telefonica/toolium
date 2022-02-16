# -*- coding: utf-8 -*-

# Copyright (c) Telefónica Digital.
# CDO QA Team <qacdo@telefonica.com>

import logging
import random
import re
import uuid

from faker import Faker
from faker_e164.providers import E164Provider
from .dataset import map_param

__logger__ = logging.getLogger(__name__)


class DataGenerator(object):
    """
    Class to generate fake data for testing.
    Supported data: street_address, email, phone_number, postal_code.
    """

    def __init__(self):
        self._provider = self._get_ob_locale()
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
        Generate random phone_number for an OB.
        If locale is not defined, return phone number from anywhere.
        """
        if self._provider: # es_ES
            region_code = self._provider.split('_')[-1]
            self._fake.add_provider(E164Provider)
            return self._fake.e164(region_code=region_code, valid=True)
        return self._fake.phone_number()

    @property
    def postal_code(self):
        """
        Generate a random OB postal code.
        """
        while True:
            postal_code = self._fake.postcode()
            if self._is_valid_postcode(self._provider, postal_code):
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
    def _get_ob_locale():
        """
        Return the OB locale.
        If property is not defined, 'es_ES' is set.
        """
        try:
            #TODO pending to implement
            return f"{map_param('[CONF:LANG]')}_{map_param('[CONF:COUNTRY]')}"
        except Exception:
            return 'es_ES'

    @staticmethod
    def _is_valid_postcode(provider, postal_code):
        """
        Validate postal codes by locale.
        Can be added custom validations for OB.
        """
        if provider == 'es_ES':
            return re.match('(?:0[1-9]|[1-4]\d|5[0-2])\d{3}$', postal_code)
        return True
