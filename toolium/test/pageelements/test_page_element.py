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
import os

import mock
import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.pageelements import PageElement, Group
from toolium.pageobjects.page_object import PageObject

child_element = 'child_element'
mock_element = None


class MenuGroup(Group):
    logo = PageElement(By.ID, 'image')
    logo_wait = PageElement(By.ID, 'image2', wait=True)


class RegisterPageObject(PageObject):
    username = PageElement(By.XPATH, '//input[0]')
    password = PageElement(By.ID, 'password', username)
    menu_group = MenuGroup(By.ID, 'menu')

    def init_page_elements(self):
        self.language = PageElement(By.ID, 'language')
        self.email = PageElement(By.ID, 'email', mock_element)
        self.address = PageElement(By.ID, 'address', (By.ID, 'parent'))
        self.address_shadowroot = PageElement(By.CSS_SELECTOR, '#address', shadowroot='shadowroot_css')
        self.address_shadowroot_by_id = PageElement(By.ID, 'address', shadowroot='shadowroot_css')
        self.element_webview = PageElement(By.ID, 'webview', webview=True)


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

    # Configure wrapper
    root_path = os.path.dirname(os.path.realpath(__file__))
    config_files = ConfigFiles()
    config_files.set_config_directory(os.path.join(root_path, 'conf'))
    config_files.set_output_directory(os.path.join(root_path, 'output'))
    config_files.set_config_log_filename('logging.conf')
    DriverWrappersPool.configure_common_directories(config_files)
    driver_wrapper.configure_properties()

    driver_wrapper.driver = mock.MagicMock()
    driver_wrapper.is_mobile_test = mock.MagicMock(return_value=False)

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


def test_get_web_element_shadowroot(driver_wrapper):
    RegisterPageObject(driver_wrapper).address_shadowroot.web_element
    expected_script = 'return document.querySelector("shadowroot_css").shadowRoot.querySelector("#address")'

    mock_element.find_element.assert_not_called()
    driver_wrapper.driver.execute_script.assert_called_once_with(expected_script)


def test_get_web_element_shadowroot_wrong_locator(driver_wrapper):
    with pytest.raises(Exception) as excinfo:
        RegisterPageObject(driver_wrapper).address_shadowroot_by_id.web_element
    assert "Locator type should be CSS_SELECTOR using shadowroot but found: id" in str(excinfo.value)
    mock_element.find_element.assert_not_called()


def test_get_web_element_in_test(driver_wrapper):
    PageElement(By.XPATH, '//input[0]').web_element

    driver_wrapper.driver.find_element.assert_called_once_with(By.XPATH, '//input[0]')


def test_get_web_element_two_times_saving_enabled(driver_wrapper):
    driver_wrapper.config.set('Driver', 'save_web_element', 'true')
    login_page = RegisterPageObject(driver_wrapper)
    login_page.username.web_element
    login_page.username.web_element

    # Check that find_element is not called the second time
    driver_wrapper.driver.find_element.assert_called_once_with(By.XPATH, '//input[0]')


def test_get_web_element_two_times_saving_disabled(driver_wrapper):
    driver_wrapper.config.set('Driver', 'save_web_element', 'false')
    login_page = RegisterPageObject(driver_wrapper)
    login_page.username.web_element
    login_page.username.web_element

    # Check that find_element is called two times
    assert driver_wrapper.driver.find_element.call_count == 2


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


def test_is_present(driver_wrapper):
    driver_wrapper.driver.find_element.return_value = mock_element

    assert RegisterPageObject(driver_wrapper).username.is_present() is True


def test_is_present_not_found(driver_wrapper):
    driver_wrapper.driver.find_element.side_effect = NoSuchElementException('Unknown')

    assert RegisterPageObject(driver_wrapper).username.is_present() is False


def test_is_visible(driver_wrapper):
    mock_element.is_displayed.return_value = True
    driver_wrapper.driver.find_element.return_value = mock_element

    assert RegisterPageObject(driver_wrapper).username.is_visible() is True


def test_is_visible_not_visible(driver_wrapper):
    mock_element.is_displayed.return_value = False
    driver_wrapper.driver.find_element.return_value = mock_element

    assert RegisterPageObject(driver_wrapper).username.is_visible() is False


def test_is_visible_not_found(driver_wrapper):
    driver_wrapper.driver.find_element.side_effect = NoSuchElementException('Unknown')

    assert RegisterPageObject(driver_wrapper).username.is_visible() is False


def test_wait_until_visible(driver_wrapper):
    driver_wrapper.utils.wait_until_element_visible = mock.MagicMock(return_value=mock_element)

    page_element = RegisterPageObject(driver_wrapper).username
    element = page_element.wait_until_visible()

    assert element == page_element


def test_wait_until_visible_exception(driver_wrapper):
    driver_wrapper.utils.wait_until_element_visible = mock.MagicMock()
    driver_wrapper.utils.wait_until_element_visible.side_effect = TimeoutException('Unknown')

    page_element = RegisterPageObject(driver_wrapper).username
    with pytest.raises(TimeoutException) as excinfo:
        page_element.wait_until_visible()
    assert "Page element of type 'PageElement' with locator ('xpath', '//input[0]') not found or is not " \
           "visible after 10 seconds" in str(excinfo.value)


def test_wait_until_visible_exception_custom_timeout(driver_wrapper):
    driver_wrapper.utils.wait_until_element_visible = mock.MagicMock()
    driver_wrapper.utils.wait_until_element_visible.side_effect = TimeoutException('Unknown')

    page_element = RegisterPageObject(driver_wrapper).username
    with pytest.raises(TimeoutException) as excinfo:
        page_element.wait_until_visible(timeout=15)
    assert "Page element of type 'PageElement' with locator ('xpath', '//input[0]') not found or is not " \
           "visible after 15 seconds" in str(excinfo.value)


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


def test_wait_until_not_visible_exception_custom_timeout(driver_wrapper):
    driver_wrapper.utils.wait_until_element_not_visible = mock.MagicMock()
    driver_wrapper.utils.wait_until_element_not_visible.side_effect = TimeoutException('Unknown')

    page_element = RegisterPageObject(driver_wrapper).username
    with pytest.raises(TimeoutException) as excinfo:
        page_element.wait_until_not_visible(timeout=15)
    assert "Page element of type 'PageElement' with locator ('xpath', '//input[0]') is still " \
           "visible after 15 seconds" in str(excinfo.value)


def test_wait_until_clickable(driver_wrapper):
    driver_wrapper.utils.wait_until_element_clickable = mock.MagicMock(return_value=mock_element)

    page_element = RegisterPageObject(driver_wrapper).username
    element = page_element.wait_until_clickable()

    assert element == page_element


def test_wait_until_clickable_exception(driver_wrapper):
    driver_wrapper.utils.wait_until_element_clickable = mock.MagicMock()
    driver_wrapper.utils.wait_until_element_clickable.side_effect = TimeoutException('Unknown')

    page_element = RegisterPageObject(driver_wrapper).username
    with pytest.raises(TimeoutException) as excinfo:
        page_element.wait_until_clickable()
    assert "Page element of type 'PageElement' with locator ('xpath', '//input[0]') not found or is not " \
           "clickable after 10 seconds" in str(excinfo.value)


def test_wait_until_clickable_exception_custom_timeout(driver_wrapper):
    driver_wrapper.utils.wait_until_element_clickable = mock.MagicMock()
    driver_wrapper.utils.wait_until_element_clickable.side_effect = TimeoutException('Unknown')

    page_element = RegisterPageObject(driver_wrapper).username
    with pytest.raises(TimeoutException) as excinfo:
        page_element.wait_until_clickable(timeout=15)
    assert "Page element of type 'PageElement' with locator ('xpath', '//input[0]') not found or is not " \
           "clickable after 15 seconds" in str(excinfo.value)


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


def test_automatic_context_selection_group(driver_wrapper):
    driver_wrapper.utils.wait_until_element_visible = mock.MagicMock(return_value=mock_element)
    driver_wrapper.is_android_test = mock.MagicMock(return_value=True)
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.context = "NATIVE_APP"
    driver_wrapper.driver.contexts = ["NATIVE_APP", "WEBVIEW"]

    RegisterPageObject(driver_wrapper).menu_group.web_element
    driver_wrapper.driver.switch_to.context.assert_not_called()
    driver_wrapper.driver.find_element.assert_called_once_with(By.ID, 'menu')


def test_android_automatic_context_selection_app_package_cap_not_available(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=True)
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.context = "NATIVE_APP"
    driver_wrapper.driver.execute_script.return_value = [{'webviewName': 'WEBVIEW_test.package.fake',
                                                          'pages': [{'id': '1234567890'}]}]
    driver_wrapper.driver.capabilities.__getitem__.side_effect = KeyError('no cap')
    driver_wrapper.driver.contexts = ["NATIVE_APP", "WEBVIEW_other.fake", "WEBVIEW_test.package.fake"]
    with pytest.raises(KeyError, match=r"no cap"):
        RegisterPageObject(driver_wrapper).element_webview.web_element


def test_ios_automatic_context_selection_bundle_id_cap_not_available(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=False)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=True)
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.context = "NATIVE_APP"
    driver_wrapper.driver.execute_script.return_value = [{'bundleId': 'test.package.fake',
                                                          'id': 'WEBVIEW_12345.1'}]
    driver_wrapper.driver.capabilities.__getitem__.side_effect = KeyError('no cap')
    driver_wrapper.driver.contexts = ["NATIVE_APP", "WEBVIEW_other.fake", "WEBVIEW_test.package.fake"]
    with pytest.raises(KeyError, match=r"no cap"):
        RegisterPageObject(driver_wrapper).element_webview.web_element


def test_android_automatic_context_selection_no_webview_context_available(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=True)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=False)
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.driver.execute_script.return_value = [{'webviewName': 'WEBVIEW_test.package.fake',
                                                          'pages': [{'id': '1234567890'}]}]
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.context = "NATIVE_APP"
    with pytest.raises(Exception) as excinfo:
        RegisterPageObject(driver_wrapper).element_webview.web_element
    assert "WEBVIEW context not found" in str(excinfo.value)


def test_ios_automatic_context_selection_no_webview_context_available(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=False)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=True)
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.driver.execute_script.return_value = [{'bundleId': 'test.package.fake',
                                                          'id': 'WEBVIEW_12345.1'}]
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.context = "NATIVE_APP"
    with pytest.raises(Exception) as excinfo:
        RegisterPageObject(driver_wrapper).element_webview.web_element
    assert "WEBVIEW context not found" in str(excinfo.value)


def test_android_automatic_context_selection_already_in_desired_webview_context_and_window(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=True)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=False)
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.capabilities = {'appPackage': 'test.package.fake'}
    driver_wrapper.driver.context = "WEBVIEW_test.package.fake"
    driver_wrapper.driver.current_window_handle = "CWindow-1234567890"
    driver_wrapper.driver.execute_script.return_value = [{'webviewName': 'WEBVIEW_test.package.fake',
                                                          'pages': [{'id': '1234567890',
                                                                     'id': '0987654321'}]}]
    RegisterPageObject(driver_wrapper).element_webview.web_element
    driver_wrapper.driver.switch_to.context.assert_not_called
    driver_wrapper.driver.switch_to.window.assert_not_called


def test_android_automatic_context_selection_already_in_desired_webview_context_but_different_window(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=True)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=False)
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.capabilities = {'appPackage': 'test.package.fake'}
    driver_wrapper.driver.context = "WEBVIEW_test.package.fake"
    driver_wrapper.driver.current_window_handle = "CDwindow-0987654321"
    driver_wrapper.driver.execute_script.return_value = [{'webviewName': 'WEBVIEW_test.package.fake',
                                                          'pages': [{'id': '1234567890'},
                                                                    {'id': '0987654321'}]}]
    RegisterPageObject(driver_wrapper).element_webview.web_element
    driver_wrapper.driver.switch_to.context.assert_not_called
    driver_wrapper.driver.switch_to.window.assert_called_once_with('CDwindow-1234567890')


def test_ios_automatic_context_selection_already_in_desired_webview_context(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=False)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=True)
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.capabilities = {'bundleId': 'test.package.fake'}
    driver_wrapper.driver.context = "WEBVIEW_12345.1"
    driver_wrapper.driver.execute_script.return_value = [{'bundleId': 'test.package.fake',
                                                          'id': 'WEBVIEW_12345.1'},
                                                         {'bundleId': 'test.package.fake',
                                                          'id': 'WEBVIEW_12345.7'},
                                                         {'bundleId': 'test.package.fake',
                                                          'id': 'WEBVIEW_54321.1'}]
    RegisterPageObject(driver_wrapper).element_webview.web_element
    driver_wrapper.driver.switch_to.context.assert_not_called


def test_android_automatic_context_selection_switch_to_new_webview_context(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=True)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=False)
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.capabilities = {'appPackage': 'test.package.fake'}
    driver_wrapper.driver.context = "WEBVIEW_other.fake.context"
    driver_wrapper.driver.current_window_handle = "CDwindow-0987654321"
    driver_wrapper.driver.execute_script.return_value = [{'webviewName': 'WEBVIEW_test.package.fake',
                                                          'pages': [{'id': '1234567890'},
                                                                    {'id': '0987654321'}]}]
    RegisterPageObject(driver_wrapper).element_webview.web_element
    driver_wrapper.driver.switch_to.context.assert_called_once_with('WEBVIEW_test.package.fake')
    driver_wrapper.driver.switch_to.window.assert_called_once_with('CDwindow-1234567890')


def test_ios_automatic_context_selection_switch_to_new_webview_context(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=False)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=True)
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.capabilities = {'bundleId': 'test.package.fake'}
    driver_wrapper.driver.context = "WEBVIEW_54321.1"
    driver_wrapper.driver.execute_script.return_value = [{'bundleId': 'test.package.fake',
                                                          'id': 'WEBVIEW_12345.1'},
                                                         {'bundleId': 'test.package.fake',
                                                          'id': 'WEBVIEW_12345.7'},
                                                         {'bundleId': 'other.package.fake',
                                                          'id': 'WEBVIEW_54321.1'}]
    RegisterPageObject(driver_wrapper).element_webview.web_element
    driver_wrapper.driver.switch_to.context.assert_called_once_with('WEBVIEW_12345.7')


def test_android_automatic_context_selection_already_in_native_context(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=True)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=False)
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.capabilities = {'appPackage': 'test.package.fake'}
    driver_wrapper.driver.context = "NATIVE_APP"
    RegisterPageObject(driver_wrapper).email
    driver_wrapper.driver.switch_to.context.assert_not_called


def test_ios_automatic_context_selection_already_in_native_context(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=False)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=True)
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.capabilities = {'appPackage': 'test.package.fake'}
    driver_wrapper.driver.context = "NATIVE_APP"
    RegisterPageObject(driver_wrapper).email
    driver_wrapper.driver.switch_to.context.assert_not_called


def test_android_automatic_context_selection_switch_to_native_context(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=True)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=False)
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.context = "WEBVIEW_test.package.fake"
    RegisterPageObject(driver_wrapper).language.web_element
    driver_wrapper.driver.switch_to.context.assert_called_once_with('NATIVE_APP')


def test_ios_automatic_context_selection_switch_to_native_context(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=False)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=True)
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.context = "WEBVIEW_12345.1"
    RegisterPageObject(driver_wrapper).language.web_element
    driver_wrapper.driver.switch_to.context.assert_called_once_with('NATIVE_APP')


def test_android_automatic_context_selection_callback_provided(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=True)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=False)
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.context = "WEBVIEW_fake.app.package"
    driver_wrapper.driver.current_window_handle = "CDwindow-0987654321"
    page_object = RegisterPageObject(driver_wrapper)
    page_object.element_webview.webview_context_selection_callback = lambda a, b: (a, b)
    page_object.element_webview.webview_csc_args = ['WEBVIEW_fake.other', "CDwindow-0123456789"]
    page_object.element_webview.web_element
    driver_wrapper.driver.switch_to.context.assert_called_once_with('WEBVIEW_fake.other')
    driver_wrapper.driver.switch_to.window.assert_called_once_with("CDwindow-0123456789")


def test_ios_automatic_context_selection_callback_provided(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=False)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=True)
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'true')
    driver_wrapper.driver.context = "WEBVIEW_12345.1"
    page_object = RegisterPageObject(driver_wrapper)
    page_object.element_webview.webview_context_selection_callback = lambda a: a
    page_object.element_webview.webview_csc_args = ['WEBVIEW_012345.67']
    page_object.element_webview.web_element
    driver_wrapper.driver.switch_to.context.assert_called_once_with('WEBVIEW_012345.67')


def test_automatic_context_selection_disabled(driver_wrapper):
    driver_wrapper.is_android_test = mock.MagicMock(return_value=True)
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=False)
    driver_wrapper.config.set('Driver', 'automatic_context_selection', 'false')
    PageElement._automatic_context_selection = mock.MagicMock()

    RegisterPageObject(driver_wrapper).element_webview.web_element
    PageElement._automatic_context_selection.assert_not_called()
    driver_wrapper.driver.find_element.assert_called_once_with(By.ID, 'webview')
