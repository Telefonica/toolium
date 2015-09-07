# -*- coding: utf-8 -*-

u"""
(c) Copyright 2015 Telefónica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefónica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefónica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
"""

import unittest

from selenium.webdriver.common.by import By
import mock

from seleniumtid.pageobjects.page_object import PageObject
from seleniumtid.pageelements import PageElement

child_element = 'child_element'
mock_element = None


@mock.patch('selenium.webdriver.remote.webelement.WebElement', spec=True)
def get_mock_element(WebElement):
    element = WebElement.return_value
    element.find_element.return_value = child_element
    return element


@mock.patch('selenium.webdriver.remote.webdriver.WebDriver')
def get_mock_driver(WebDriver):
    driver = WebDriver.return_value
    driver.find_element.return_value = mock_element
    return driver


class LoginPageObject(PageObject):
    username = PageElement(By.NAME, 'username')
    password = PageElement(By.ID, 'password', username)

class RegisterPageObject(PageObject):
    username = PageElement(By.NAME, 'username')
    password = PageElement(By.ID, 'password', username)

    def init_page_elements(self):
        self.email = PageElement(By.ID, 'email', mock_element)

class TestPageElement(unittest.TestCase):
    def setUp(self):
        """Create a new mock element and a new driver before each test"""
        global mock_element
        mock_element = get_mock_element()
        self.driver = get_mock_driver()

    def test_locator(self):
        page_element = LoginPageObject(self.driver)

        self.assertEquals(page_element.username.locator, (By.NAME, 'username'))
        self.assertEquals(page_element.password.locator, (By.ID, 'password'))

    def test_get_element(self):
        page_element = LoginPageObject(self.driver)
        web_element = page_element.username.element()

        self.assertEquals(web_element, mock_element)
        self.assertEquals(self.driver.find_element.mock_calls, [mock.call(By.NAME, 'username')])

    def test_get_element_with_parent(self):
        page_element = LoginPageObject(self.driver)
        web_element = page_element.password.element()

        self.assertEquals(web_element, child_element)
        self.assertEquals(self.driver.find_element.mock_calls, [mock.call(By.NAME, 'username')])
        self.assertEquals(mock_element.find_element.mock_calls, [mock.call(By.ID, 'password')])

    def test_get_element_with_parent_webelement(self):
        page_element = RegisterPageObject(self.driver)
        web_element = page_element.email.element()

        self.assertEquals(web_element, child_element)
        self.assertEquals(self.driver.find_element.mock_calls, [])
        self.assertEquals(mock_element.find_element.mock_calls, [mock.call(By.ID, 'email')])
