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
from nose.tools import assert_equal, assert_is_not_none, assert_is_none, assert_raises, assert_in
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.pageelements import PageElement
from toolium.pageobjects.page_object import PageObject

child_element = 'child_element'
mock_element = None


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
        mock_element = mock.MagicMock(spec=WebElement)
        mock_element.find_element.return_value = child_element

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

    def test_get_web_element(self):
        RegisterPageObject().username.web_element

        self.driver_wrapper.driver.find_element.assert_called_with(By.XPATH, '//input[0]')

    def test_get_web_element_init_page(self):
        RegisterPageObject().language.web_element

        self.driver_wrapper.driver.find_element.assert_called_with(By.ID, 'language')

    def test_get_web_element_with_parent(self):
        self.driver_wrapper.driver.find_element.return_value = mock_element
        web_element = RegisterPageObject().password.web_element

        assert_equal(web_element, child_element)
        self.driver_wrapper.driver.find_element.assert_called_with(By.XPATH, '//input[0]')
        mock_element.find_element.assert_called_with(By.ID, 'password')

    def test_get_web_element_with_parent_locator(self):
        self.driver_wrapper.driver.find_element.return_value = mock_element
        web_element = RegisterPageObject().address.web_element

        assert_equal(web_element, child_element)
        self.driver_wrapper.driver.find_element.assert_called_with(By.ID, 'parent')
        mock_element.find_element.assert_called_with(By.ID, 'address')

    def test_get_web_element_with_parent_web_element(self):
        web_element = RegisterPageObject().email.web_element

        assert_equal(web_element, child_element)
        self.driver_wrapper.driver.find_element.assert_not_called()
        mock_element.find_element.assert_called_with(By.ID, 'email')

    def test_get_web_element_in_test(self):
        PageElement(By.XPATH, '//input[0]').web_element

        self.driver_wrapper.driver.find_element.assert_called_with(By.XPATH, '//input[0]')

    def test_get_web_element_two_times(self):
        login_page = RegisterPageObject()
        login_page.username.web_element
        login_page.username.web_element

        # Check that find_element is not called the second time
        self.driver_wrapper.driver.find_element.assert_called_with(By.XPATH, '//input[0]')

    def test_get_web_element_two_elements(self):
        login_page = RegisterPageObject()
        login_page.username.web_element
        login_page.language.web_element

        # Check that find_element is called two times
        self.driver_wrapper.driver.find_element.assert_has_calls(
            [mock.call(By.XPATH, '//input[0]'), mock.call(By.ID, 'language')])

    def test_get_web_element_two_objects(self):
        login_page = RegisterPageObject()
        login_page.language.web_element
        second_login_page = RegisterPageObject()
        second_login_page.language.web_element

        # Check that find_element is called two times
        self.driver_wrapper.driver.find_element.assert_has_calls(
            [mock.call(By.ID, 'language'), mock.call(By.ID, 'language')])

    def test_get_web_element_exception(self):
        self.driver_wrapper.driver.find_element.side_effect = NoSuchElementException('Unknown')

        with assert_raises(NoSuchElementException) as cm:
            RegisterPageObject().username.web_element
        assert_in("Page element of type 'PageElement' with locator ('xpath', '//input[0]') not found",
                  str(cm.exception))

    def test_wait_until_visible(self):
        self.driver_wrapper.utils.wait_until_element_visible = mock.MagicMock(return_value=mock_element)

        page_element = RegisterPageObject().username
        element = page_element.wait_until_visible()

        assert_equal(element._web_element, mock_element)
        assert_equal(element, page_element)

    def test_wait_until_visible_exception(self):
        self.driver_wrapper.utils.wait_until_element_visible = mock.MagicMock()
        self.driver_wrapper.utils.wait_until_element_visible.side_effect = TimeoutException('Unknown')

        page_element = RegisterPageObject().username
        with assert_raises(TimeoutException) as cm:
            page_element.wait_until_visible()
        assert_in("Page element of type 'PageElement' with locator ('xpath', '//input[0]') not found or is not "
                  "visible after 10 seconds", str(cm.exception))

    def test_wait_until_not_visible(self):
        self.driver_wrapper.utils.wait_until_element_not_visible = mock.MagicMock(return_value=False)

        page_element = RegisterPageObject().username
        element = page_element.wait_until_not_visible()

        assert_is_none(element._web_element)
        assert_equal(element, page_element)

    def test_wait_until_not_visible_exception(self):
        self.driver_wrapper.utils.wait_until_element_not_visible = mock.MagicMock()
        self.driver_wrapper.utils.wait_until_element_not_visible.side_effect = TimeoutException('Unknown')

        page_element = RegisterPageObject().username
        with assert_raises(TimeoutException) as cm:
            page_element.wait_until_not_visible()
        assert_in("Page element of type 'PageElement' with locator ('xpath', '//input[0]') is still "
                  "visible after 10 seconds", str(cm.exception))

    @mock.patch('toolium.visual_test.VisualTest.__init__', return_value=None)
    @mock.patch('toolium.visual_test.VisualTest.assert_screenshot')
    def test_assert_screenshot(self, visual_assert_screenshot, visual_init):
        self.driver_wrapper.driver.find_element.return_value = mock_element

        RegisterPageObject().username.assert_screenshot('filename')

        visual_init.assert_called_with(self.driver_wrapper, False)
        visual_assert_screenshot.assert_called_with(mock_element, 'filename', 'PageElement', 0, [])

    @mock.patch('toolium.visual_test.VisualTest.__init__', return_value=None)
    @mock.patch('toolium.visual_test.VisualTest.assert_screenshot')
    def test_assert_screenshot_options(self, visual_assert_screenshot, visual_init):
        self.driver_wrapper.driver.find_element.return_value = mock_element

        RegisterPageObject().username.assert_screenshot('filename', threshold=0.1, exclude_elements=[mock_element],
                                                        force=True)

        visual_init.assert_called_with(self.driver_wrapper, True)
        visual_assert_screenshot.assert_called_with(mock_element, 'filename', 'PageElement', 0.1, [mock_element])

    def test_get_attribute(self):
        self.driver_wrapper.driver.find_element.return_value = mock_element

        RegisterPageObject().username.get_attribute('attribute_name')

        mock_element.get_attribute.assert_called_with('attribute_name')
