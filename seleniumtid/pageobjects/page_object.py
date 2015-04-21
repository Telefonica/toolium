# -*- coding: utf-8 -*-
'''
(c) Copyright 2014 Telefonica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefonica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefonica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
'''
import unittest
import logging

from seleniumtid import selenium_driver
from seleniumtid.pageelements.page_element import PageElement
from seleniumtid.test_cases import AppiumTestCase


class PageObject(unittest.TestCase):
    def __init__(self, driver=None):
        self.logger = logging.getLogger(__name__)
        self._driver = driver if driver else selenium_driver.driver
        self.config = selenium_driver.config
        self.app_strings = AppiumTestCase.app_strings
        self.init_page_elements()
        if driver:
            self._update_page_elements_driver()

    @property
    def driver(self):
        '''
        This method allows to autocomplete self.driver in IDEs
        :rtype selenium.webdriver.remote.webdriver.WebDriver
        '''
        return self._driver

    def init_page_elements(self):
        '''
        Method to initialize page elements
        Must be overridden by subclasses
        '''
        pass

    def _update_page_elements_driver(self):
        '''
        Assign driver to all page elements of this page object
        '''
        for element in self.__dict__.values():
            if isinstance(element, PageElement):
                element.set_driver(self.driver)
