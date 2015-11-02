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

import unittest
import logging

from toolium import toolium_driver
from toolium.pageelements.page_element import PageElement
from toolium.test_cases import AppiumTestCase
from toolium.utils import Utils


class PageObject(unittest.TestCase):
    """
    :type driver: selenium.webdriver.remote.webdriver.WebDriver
    :type utils: toolium.utils.Utils
    """

    def __init__(self, driver=None):
        self.logger = logging.getLogger(__name__)
        self.driver = driver if driver else toolium_driver.driver
        self.utils = Utils(self.driver)
        self.config = toolium_driver.config
        self.app_strings = AppiumTestCase.app_strings
        self.init_page_elements()
        self._update_page_elements()

    def set_driver(self, driver):
        """Set Selenium driver"""
        self.driver = driver

    def set_utils(self, utils):
        """Set utils instance"""
        self.utils = utils

    def init_page_elements(self):
        """Method to initialize page elements"""
        pass

    def _update_page_elements(self):
        """Copy driver and utils instances to all page elements of this page object"""
        for element in self.__dict__.values() + self.__class__.__dict__.values():
            if isinstance(element, PageElement):
                element.set_driver(self.driver)
                element.set_utils(self.utils)
            if isinstance(element, PageObject):
                element.set_driver(self.driver)
                element.set_utils(self.utils)
                # If element is page object, update its page elements
                element._update_page_elements()