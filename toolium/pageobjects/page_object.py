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

import logging
import unittest

from toolium import toolium_driver
from toolium.pageelements.page_element import PageElement
from toolium.test_cases import AppiumTestCase
from toolium.utils import Utils


class PageObject(unittest.TestCase):
    """
    :type driver: selenium.webdriver.remote.webdriver.WebDriver
    :type utils: toolium.utils.Utils
    """

    def __init__(self, driver_wrapper=None):
        """Initialize page object properties and update their page elements

        :param driver_wrapper: driver wrapper instance
        """
        self.logger = logging.getLogger(__name__)
        self.driver_wrapper = driver_wrapper if driver_wrapper else toolium_driver
        self.driver = self.driver_wrapper.driver
        self.config = self.driver_wrapper.config
        self.utils = Utils(self.driver)
        self.app_strings = AppiumTestCase.app_strings
        self.init_page_elements()
        self._update_page_elements()

    def set_driver(self, driver):
        """Set Selenium driver"""
        self.driver = driver

    def set_utils(self, utils):
        """Set utils instance"""
        self.utils = utils

    def set_config(self, config):
        """Set configuration properties"""
        self.config = config

    def init_page_elements(self):
        """Method to initialize page elements"""
        pass

    def _update_page_elements(self):
        """Copy driver and utils instances to all page elements of this page object"""
        for element in list(self.__dict__.values()) + list(self.__class__.__dict__.values()):
            if isinstance(element, PageElement):
                element.set_driver(self.driver)
                element.set_utils(self.utils)
            if isinstance(element, PageObject):
                element.set_driver(self.driver)
                element.set_utils(self.utils)
                element.set_config(self.config)
                # If element is page object, update its page elements
                element._update_page_elements()
