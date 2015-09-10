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

from selenium.webdriver.remote.webelement import WebElement


class PageElement(object):
    """
    :type driver: selenium.webdriver.remote.webdriver.WebDriver
    :type utils: seleniumtid.utils.Utils
    """
    driver = None
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

    def set_driver(self, driver):
        """Set Selenium driver"""
        self.driver = driver

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
