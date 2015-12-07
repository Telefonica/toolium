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

from selenium.webdriver.remote.webelement import WebElement

from toolium import toolium_wrapper
from toolium.utils import Utils
from toolium.visual_test import VisualTest


class PageElement(object):
    """
    :type driver_wrapper: toolium.driver_wrapper.DriverWrapper
    :type driver: selenium.webdriver.remote.webdriver.WebDriver
    :type config: toolium.config_parser.ExtendedConfigParser
    :type utils: toolium.utils.Utils
    """
    driver_wrapper = None
    driver = None
    config = None
    utils = None

    def __init__(self, by, value, parent=None):
        """Initialize the PageElement object with the given locator components.

        If parent is not None, find_element will be performed over it, instead of
        using the driver's method, so it can find nested elements.

        :param by: locator type
        :param value: locator value
        :param parent: parent element (WebElement or PageElement)
        """
        self.locator = (by, value)
        self.parent = parent
        self.set_driver_wrapper()

    def set_driver_wrapper(self, driver_wrapper=None):
        """Initialize driver_wrapper, driver, config and utils

        :param driver_wrapper: driver wrapper instance
        """
        self.driver_wrapper = driver_wrapper if driver_wrapper else toolium_wrapper
        self.set_driver(self.driver_wrapper.driver)
        self.set_config(self.driver_wrapper.config)
        self.set_utils(Utils(self.driver_wrapper))

    def set_driver(self, driver):
        """Set Selenium driver"""
        self.driver = driver

    def set_config(self, config):
        """Set configuration properties"""
        self.config = config

    def set_utils(self, utils):
        """Set utils instance"""
        self.utils = utils

    def element(self):
        """Find WebElement using element locator

        :return: web element object
        :rtype: selenium.webdriver.remote.webelement.WebElement
        """
        if self.parent and isinstance(self.parent, WebElement):
            return self.parent.find_element(*self.locator)
        if self.parent and isinstance(self.parent, PageElement):
            return self.parent.element().find_element(*self.locator)
        return self.driver.find_element(*self.locator)

    def scroll_element_into_view(self):
        """Scroll element into view"""
        y = self.element().location['y']
        self.driver.execute_script('window.scrollTo(0, {0})'.format(y))

    def wait_until_visible(self, timeout=10):
        """Search element and wait until it is visible

        :param timeout: max time to wait
        :returns: web element if it is visible or False
        """
        return self.utils.wait_until_element_visible(self.locator, timeout)

    def wait_until_not_visible(self, timeout=10):
        """Search element and wait until it is not visible

        :param timeout: max time to wait
        :returns: web element if it is not visible or False
        """
        return self.utils.wait_until_element_not_visible(self.locator, timeout)

    def assertScreenshot(self, filename, threshold=0, exclude_elements=[]):
        """Assert that a screenshot of the element is the same as a screenshot on disk, within a given threshold.

        :param filename: the filename for the screenshot, which will be appended with ``.png``
        :param threshold: the threshold for triggering a test failure
        :param exclude_elements: list of CSS/XPATH selectors as a string or WebElement objects that must be excluded
                                 from the assertion.
        """
        VisualTest(self.driver_wrapper).assertScreenshot(self.element(), filename, self.__class__.__name__, threshold,
                                                         exclude_elements)
