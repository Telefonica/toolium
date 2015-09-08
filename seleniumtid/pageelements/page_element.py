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

from seleniumtid import selenium_driver


class PageElement(object):
    def __init__(self, by, value, parent=None):
        """Initialize the PageElement object with the given locator components.

        If parent is not None, find_element will be performed over it, instead of
        using the driver's method, so it can find nested elements.

        :param by: locator type
        :param value: locator value
        :param parent: parent element (WebElement or PageElement)
        """
        self.locator = (by, value)
        self._driver = None
        self.parent = parent

    @property
    def driver(self):
        """Get the Selenium driver
         This method allows to autocomplete self.driver in IDEs

        :returns: Selenium driver
        :rtype: selenium.webdriver.remote.webdriver.WebDriver
        """
        return self._driver

    def set_driver(self, driver):
        self._driver = driver

    def element(self):
        """Find WebElement using element locator
        :return: web element object
        :rtype selenium.webdriver.remote.webelement.WebElement
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
