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
from seleniumtid.pageelements import input_text_page_element, select_page_element
from seleniumtid.pageelements import *

child_element = 'child_element'
mock_element = None


@mock.patch('selenium.webdriver.remote.webelement.WebElement', spec=True)
def get_mock_element(WebElement):
    element = WebElement.return_value
    element.find_element.return_value = child_element
    element.text = 'text value'
    element.get_attribute.return_value = 'input text value'
    return element


@mock.patch('selenium.webdriver.remote.webdriver.WebDriver')
def get_mock_driver(WebDriver):
    driver = WebDriver.return_value
    driver.find_element.return_value = mock_element
    return driver


def get_mock_select():
    # Mock text property
    mock_prop_text = mock.PropertyMock(return_value='option value')
    mock_text = mock.MagicMock()
    type(mock_text).text = mock_prop_text
    # Mock first_selected_option property
    mock_prop_option = mock.PropertyMock(return_value=mock_text)
    mock_option = mock.MagicMock()
    type(mock_option).first_selected_option = mock_prop_option
    # Mock select
    mock_select = mock.MagicMock(return_value=mock_option)
    return mock_select


class LoginPageObject(PageObject):
    title = Text(By.ID, 'title')
    username = InputText(By.ID, 'username')
    password = InputText(By.ID, 'password')
    language = Select(By.ID, 'language')
    login = Button(By.ID, 'login')


class TestPageElements(unittest.TestCase):
    def setUp(self):
        """Create a new mock element and a new driver before each test"""
        global mock_element
        mock_element = get_mock_element()
        self.driver = get_mock_driver()

    def test_locator(self):
        page_object = LoginPageObject(self.driver)

        self.assertEquals(page_object.title.locator, (By.ID, 'title'))
        self.assertEquals(page_object.username.locator, (By.ID, 'username'))
        self.assertEquals(page_object.password.locator, (By.ID, 'password'))
        self.assertEquals(page_object.language.locator, (By.ID, 'language'))
        self.assertEquals(page_object.login.locator, (By.ID, 'login'))

    def test_get_text(self):
        page_object = LoginPageObject(self.driver)
        title_value = page_object.title.text

        self.assertEquals(title_value, 'text value')

    def test_get_inputtext(self):
        page_object = LoginPageObject(self.driver)
        username_value = page_object.username.text

        self.assertEquals(username_value, 'input text value')

    def test_set_inputtext(self):
        input_text_page_element.selenium_driver.is_ios_test = mock.MagicMock(return_value=False)

        page_object = LoginPageObject(self.driver)
        page_object.username.text = 'new input value'

        self.assertEquals(mock_element.send_keys.mock_calls, [mock.call('new input value')])

    def test_get_selected_option(self):
        select_page_element.SeleniumSelect = get_mock_select()

        page_object = LoginPageObject(self.driver)
        option = page_object.language.option

        self.assertEquals(option, 'option value')

    def test_select_option(self):
        select_page_element.SeleniumSelect = get_mock_select()

        page_object = LoginPageObject(self.driver)
        page_object.language.option = 'new option value'

        self.assertEquals(len(select_page_element.SeleniumSelect.mock_calls), 1)
        self.assertEquals(select_page_element.SeleniumSelect().mock_calls,
                          [mock.call.select_by_visible_text('new option value')])

    def test_click_button(self):
        page_object = LoginPageObject(self.driver)
        page_object.login.click()

        self.assertEquals(mock_element.click.mock_calls, [mock.call()])

