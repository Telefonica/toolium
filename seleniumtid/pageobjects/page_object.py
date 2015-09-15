# -*- coding: utf-8 -*-

u"""
(c) Copyright 2014 Telefónica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefónica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefónica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
"""

import unittest
import logging

from seleniumtid import selenium_driver
from seleniumtid.pageelements.page_element import PageElement
from seleniumtid.test_cases import AppiumTestCase
from seleniumtid.utils import Utils


class PageObject(unittest.TestCase):
    """
    :type driver: selenium.webdriver.remote.webdriver.WebDriver
    :type utils: seleniumtid.utils.Utils
    """

    def __init__(self, driver=None):
        self.logger = logging.getLogger(__name__)
        self.driver = driver if driver else selenium_driver.driver
        self.utils = Utils(self.driver)
        self.config = selenium_driver.config
        self.app_strings = AppiumTestCase.app_strings
        self.init_page_elements()
        self._update_page_elements()

    def init_page_elements(self):
        """Method to initialize page elements"""
        pass

    def _update_page_elements(self):
        """Copy driver and utils instances to all page elements of this page object"""
        for element in self.__dict__.values() + self.__class__.__dict__.values():
            if isinstance(element, PageElement):
                element.set_driver(self.driver)
                element.set_utils(self.utils)
