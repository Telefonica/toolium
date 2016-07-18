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

import mock
import pytest
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


@pytest.fixture
def driver_wrapper():
    """Create a new mock element and a new driver before each test"""
    global mock_element
    mock_element = mock.MagicMock(spec=WebElement)
    mock_element.find_element.return_value = child_element

    # Reset wrappers pool values
    DriverWrappersPool._empty_pool()
    DriverWrapper.config_properties_filenames = None

    # Create a new wrapper
    driver_wrapper = DriverWrappersPool.get_default_wrapper()
    driver_wrapper.driver = mock.MagicMock()

    return driver_wrapper


def test_locator(driver_wrapper):
    page_object = RegisterPageObject(driver_wrapper)

    assert page_object.username.locator == (By.XPATH, '//input[0]')
    assert page_object.password.locator == (By.ID, 'password')


def test_reset_object(driver_wrapper):
    login_page = RegisterPageObject(driver_wrapper)
    login_page.username.web_element
    login_page.language.web_element

    # Check that web elements are filled
    assert login_page.username._web_element is not None
    assert login_page.language._web_element is not None

    login_page.username.reset_object()

    # Check that only username is reset
    assert login_page.username._web_element is None
    assert login_page.language._web_element is not None


def test_reset_object_two_page_objects(driver_wrapper):
    login_page = RegisterPageObject(driver_wrapper)
    login_page.language.web_element
    second_login_page = RegisterPageObject(driver_wrapper)
    second_login_page.language.web_element

    # Check that web elements are filled
    assert login_page.language._web_element is not None
    assert second_login_page.language._web_element is not None

    login_page.language.reset_object()

    # Check that only first language is reset
    assert login_page.language._web_element is None
    assert second_login_page.language._web_element is not None


def test_get_web_element(driver_wrapper):
    RegisterPageObject(driver_wrapper).username.web_element

    driver_wrapper.driver.find_element.assert_called_once_with(By.XPATH, '//input[0]')


def test_get_web_element_init_page(driver_wrapper):
    RegisterPageObject(driver_wrapper).language.web_element

    driver_wrapper.driver.find_element.assert_called_once_with(By.ID, 'language')


def test_get_web_element_with_parent(driver_wrapper):
    driver_wrapper.driver.find_element.return_value = mock_element
    web_element = RegisterPageObject(driver_wrapper).password.web_element

    assert web_element == child_element
    driver_wrapper.driver.find_element.assert_called_once_with(By.XPATH, '//input[0]')
    mock_element.find_element.assert_called_once_with(By.ID, 'password')


def test_get_web_element_with_parent_locator(driver_wrapper):
    driver_wrapper.driver.find_element.return_value = mock_element
    web_element = RegisterPageObject(driver_wrapper).address.web_element

    assert web_element == child_element
    driver_wrapper.driver.find_element.assert_called_once_with(By.ID, 'parent')
    mock_element.find_element.assert_called_once_with(By.ID, 'address')


def test_get_web_element_with_parent_web_element(driver_wrapper):
    web_element = RegisterPageObject(driver_wrapper).email.web_element

    assert web_element == child_element
    driver_wrapper.driver.find_element.assert_not_called()
    mock_element.find_element.assert_called_once_with(By.ID, 'email')


def test_get_web_element_in_test(driver_wrapper):
    PageElement(By.XPATH, '//input[0]').web_element

    driver_wrapper.driver.find_element.assert_called_once_with(By.XPATH, '//input[0]')


def test_get_web_element_two_times(driver_wrapper):
    login_page = RegisterPageObject(driver_wrapper)
    login_page.username.web_element
    login_page.username.web_element

    # Check that find_element is not called the second time
    driver_wrapper.driver.find_element.assert_called_once_with(By.XPATH, '//input[0]')


def test_get_web_element_two_elements(driver_wrapper):
    login_page = RegisterPageObject(driver_wrapper)
    login_page.username.web_element
    login_page.language.web_element

    # Check that find_element is called two times
    driver_wrapper.driver.find_element.assert_has_calls(
        [mock.call(By.XPATH, '//input[0]'), mock.call(By.ID, 'language')])


def test_get_web_element_two_objects(driver_wrapper):
    login_page = RegisterPageObject(driver_wrapper)
    login_page.language.web_element
    second_login_page = RegisterPageObject(driver_wrapper)
    second_login_page.language.web_element

    # Check that find_element is called two times
    driver_wrapper.driver.find_element.assert_has_calls(
        [mock.call(By.ID, 'language'), mock.call(By.ID, 'language')])


def test_get_web_element_exception(driver_wrapper):
    driver_wrapper.driver.find_element.side_effect = NoSuchElementException('Unknown')

    with pytest.raises(NoSuchElementException) as excinfo:
        RegisterPageObject(driver_wrapper).username.web_element
    assert "Page element of type 'PageElement' with locator ('xpath', '//input[0]') not found" in str(excinfo.value)


def test_wait_until_visible(driver_wrapper):
    driver_wrapper.utils.wait_until_element_visible = mock.MagicMock(return_value=mock_element)

    page_element = RegisterPageObject(driver_wrapper).username
    element = page_element.wait_until_visible()

    assert element._web_element == mock_element
    assert element == page_element


def test_wait_until_visible_exception(driver_wrapper):
    driver_wrapper.utils.wait_until_element_visible = mock.MagicMock()
    driver_wrapper.utils.wait_until_element_visible.side_effect = TimeoutException('Unknown')

    page_element = RegisterPageObject(driver_wrapper).username
    with pytest.raises(TimeoutException) as excinfo:
        page_element.wait_until_visible()
    assert "Page element of type 'PageElement' with locator ('xpath', '//input[0]') not found or is not " \
           "visible after 10 seconds" in str(excinfo.value)


def test_wait_until_not_visible(driver_wrapper):
    driver_wrapper.utils.wait_until_element_not_visible = mock.MagicMock(return_value=False)

    page_element = RegisterPageObject(driver_wrapper).username
    element = page_element.wait_until_not_visible()

    assert element._web_element is None
    assert element == page_element


def test_wait_until_not_visible_exception(driver_wrapper):
    driver_wrapper.utils.wait_until_element_not_visible = mock.MagicMock()
    driver_wrapper.utils.wait_until_element_not_visible.side_effect = TimeoutException('Unknown')

    page_element = RegisterPageObject(driver_wrapper).username
    with pytest.raises(TimeoutException) as excinfo:
        page_element.wait_until_not_visible()
    assert "Page element of type 'PageElement' with locator ('xpath', '//input[0]') is still " \
           "visible after 10 seconds" in str(excinfo.value)


@mock.patch('toolium.visual_test.VisualTest.__init__', return_value=None)
@mock.patch('toolium.visual_test.VisualTest.assert_screenshot')
def test_assert_screenshot(visual_assert_screenshot, visual_init, driver_wrapper):
    driver_wrapper.driver.find_element.return_value = mock_element

    RegisterPageObject(driver_wrapper).username.assert_screenshot('filename')

    visual_init.assert_called_once_with(driver_wrapper, False)
    visual_assert_screenshot.assert_called_once_with(mock_element, 'filename', 'PageElement', 0, [])


@mock.patch('toolium.visual_test.VisualTest.__init__', return_value=None)
@mock.patch('toolium.visual_test.VisualTest.assert_screenshot')
def test_assert_screenshot_options(visual_assert_screenshot, visual_init, driver_wrapper):
    driver_wrapper.driver.find_element.return_value = mock_element

    RegisterPageObject(driver_wrapper).username.assert_screenshot('filename', threshold=0.1,
                                                                  exclude_elements=[mock_element],
                                                                  force=True)

    visual_init.assert_called_once_with(driver_wrapper, True)
    visual_assert_screenshot.assert_called_once_with(mock_element, 'filename', 'PageElement', 0.1, [mock_element])


def test_get_attribute(driver_wrapper):
    driver_wrapper.driver.find_element.return_value = mock_element

    RegisterPageObject(driver_wrapper).username.get_attribute('attribute_name')

    mock_element.get_attribute.assert_called_once_with('attribute_name')
