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

import mock
import six
from nose.tools import assert_equal, assert_is_not_none, assert_is_none
from selenium.webdriver.common.by import By

from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.pageelements import PageElement
from toolium.pageobjects.page_object import PageObject

child_element = 'child_element'
mock_element = None


@mock.patch('selenium.webdriver.remote.webelement.WebElement', spec=True)
def get_mock_element(WebElement):
    web_element = WebElement.return_value
    web_element.find_element.return_value = child_element
    return web_element


class RegisterPageObject(PageObject):
    username = PageElement(By.XPATH, '//input[0]')
    password = PageElement(By.ID, 'password', username)

    def init_page_elements(self):
        self.language = PageElement(By.ID, 'language')
        self.email = PageElement(By.ID, 'email', mock_element)
        self.address = PageElement(By.ID, 'address', (By.ID, 'parent'))


class TestPageElement(unittest.TestCase):
    def setUp(self):
        """Create a new mock element and a new driver before each test"""
        global mock_element
        mock_element = get_mock_element()

        # Reset wrappers pool values
        DriverWrappersPool._empty_pool()
        DriverWrapper.config_properties_filenames = None

        # Create a new wrapper
        self.driver_wrapper = DriverWrappersPool.get_default_wrapper()
        self.driver_wrapper.driver = mock.MagicMock()

    def test_locator(self):
        page_object = RegisterPageObject()

        assert_equal(page_object.username.locator, (By.XPATH, '//input[0]'))
        assert_equal(page_object.password.locator, (By.ID, 'password'))

    def test_get_web_element(self):
        RegisterPageObject().username.web_element

        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [mock.call(By.XPATH, '//input[0]')])

    def test_get_web_element_init_page(self):
        RegisterPageObject().language.web_element

        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [mock.call(By.ID, 'language')])

    def test_get_web_element_with_parent(self):
        self.driver_wrapper.driver.find_element.return_value = mock_element
        web_element = RegisterPageObject().password.web_element

        assert_equal(web_element, child_element)
        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [mock.call(By.XPATH, '//input[0]')])
        assert_equal(mock_element.find_element.mock_calls, [mock.call(By.ID, 'password')])

    def test_get_web_element_with_parent_locator(self):
        self.driver_wrapper.driver.find_element.return_value = mock_element
        web_element = RegisterPageObject().address.web_element

        assert_equal(web_element, child_element)
        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [mock.call(By.ID, 'parent')])
        assert_equal(mock_element.find_element.mock_calls, [mock.call(By.ID, 'address')])

    def test_get_web_element_with_parent_web_element(self):
        web_element = RegisterPageObject().email.web_element

        assert_equal(web_element, child_element)
        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [])
        assert_equal(mock_element.find_element.mock_calls, [mock.call(By.ID, 'email')])

    def test_get_web_element_in_test(self):
        PageElement(By.XPATH, '//input[0]').web_element

        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [mock.call(By.XPATH, '//input[0]')])

    def test_get_web_element_two_times(self):
        login_page = RegisterPageObject()
        login_page.username.web_element
        login_page.username.web_element

        # Check that find_element is not called the second time
        if six.PY2:
            second_call = mock.call().__nonzero__()
        else:
            second_call = mock.call().__bool__()
        assert_equal(self.driver_wrapper.driver.find_element.mock_calls,
                     [mock.call(By.XPATH, '//input[0]'), second_call])

    def test_get_web_element_two_elements(self):
        login_page = RegisterPageObject()
        login_page.username.web_element
        login_page.language.web_element

        # Check that find_element is called two times
        assert_equal(self.driver_wrapper.driver.find_element.mock_calls,
                     [mock.call(By.XPATH, '//input[0]'), mock.call(By.ID, 'language')])

    def test_get_web_element_two_objects(self):
        login_page = RegisterPageObject()
        login_page.language.web_element
        second_login_page = RegisterPageObject()
        second_login_page.language.web_element

        # Check that find_element is called two times
        assert_equal(self.driver_wrapper.driver.find_element.mock_calls,
                     [mock.call(By.ID, 'language'), mock.call(By.ID, 'language')])

    def test_reset_object(self):
        login_page = RegisterPageObject()
        login_page.username.web_element
        login_page.language.web_element

        # Check that web elements are filled
        assert_is_not_none(login_page.username._web_element)
        assert_is_not_none(login_page.language._web_element)

        login_page.username.reset_object()

        # Check that only username is reset
        assert_is_none(login_page.username._web_element)
        assert_is_not_none(login_page.language._web_element)

    def test_reset_object_two_page_objects(self):
        login_page = RegisterPageObject()
        login_page.language.web_element
        second_login_page = RegisterPageObject()
        second_login_page.language.web_element

        # Check that web elements are filled
        assert_is_not_none(login_page.language._web_element)
        assert_is_not_none(second_login_page.language._web_element)

        login_page.language.reset_object()

        # Check that only first language is reset
        assert_is_none(login_page.language._web_element)
        assert_is_not_none(second_login_page.language._web_element)
