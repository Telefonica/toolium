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

from seleniumtid import selenium_driver


class PageElement(object):
    def __init__(self, by, value):
        self.locator = (by, value)
        self._driver = selenium_driver.driver

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
        """
        :return: web element object
        :rtype selenium.webdriver.remote.webelement.WebElement
        """
        return self.driver.find_element(*self.locator)
