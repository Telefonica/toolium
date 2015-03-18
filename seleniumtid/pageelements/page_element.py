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
from seleniumtid import selenium_driver


class PageElement(object):
    def __init__(self, by, value):
        self.locator = (by, value)
        self._driver = selenium_driver.driver

    @property
    def driver(self):
        '''
        This method allows to autocomplete self.driver in IDEs
        :rtype selenium.webdriver.remote.webdriver.WebDriver
        '''
        return self._driver

    def set_driver(self, driver):
        self._driver = driver

    def element(self):
        """
        :return: web element object
        :rtype selenium.webdriver.remote.webelement.WebElement
        """
        return self.driver.find_element(*self.locator)
