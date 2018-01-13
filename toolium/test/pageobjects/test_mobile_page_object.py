# -*- coding: utf-8 -*-
u"""
Copyright 2016 Telefónica Investigación y Desarrollo, S.A.U.
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

import pytest

from toolium.config_files import ConfigFiles
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.test.pageobjects.examples.android.login import AndroidLoginPageObject
from toolium.test.pageobjects.examples.base.login import BaseLoginPageObject
from toolium.test.pageobjects.examples.ios.login import IosLoginPageObject
from toolium.test.pageobjects.examples.login_one_file import AndroidLoginOneFilePageObject, IosLoginOneFilePageObject
from toolium.test.pageobjects.examples.login_one_file import BaseLoginOneFilePageObject


@pytest.fixture
def driver_wrapper():
    # Configure properties
    config_files = ConfigFiles()
    root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    config_files.set_config_directory(os.path.join(root_path, 'conf'))
    config_files.set_config_properties_filenames('properties.cfg')
    driver_wrapper = DriverWrappersPool.get_default_wrapper()
    driver_wrapper.configure(config_files)

    return driver_wrapper


def test_mobile_page_object_ios(driver_wrapper):
    driver_wrapper.config.set('Driver', 'type', 'ios')
    page_object = BaseLoginPageObject(driver_wrapper)

    # Check instance type, specific locator and common method
    assert isinstance(page_object, IosLoginPageObject)
    assert page_object.username.locator[1] == 'username_id_ios'
    assert hasattr(page_object, 'login')


def test_mobile_page_object_android(driver_wrapper):
    driver_wrapper.config.set('Driver', 'type', 'android')
    page_object = BaseLoginPageObject(driver_wrapper)

    # Check instance type, specific locator and common method
    assert isinstance(page_object, AndroidLoginPageObject)
    assert page_object.username.locator[1] == 'username_id_android'
    assert hasattr(page_object, 'login')


def test_mobile_page_object_default(driver_wrapper):
    driver_wrapper.config.set('Driver', 'type', 'unknown')
    page_object = BaseLoginPageObject(driver_wrapper)

    # Check instance type, specific locator and common method
    assert isinstance(page_object, AndroidLoginPageObject)
    assert page_object.username.locator[1] == 'username_id_android'
    assert hasattr(page_object, 'login')


def test_mobile_page_object_one_file_ios(driver_wrapper):
    driver_wrapper.config.set('Driver', 'type', 'ios')
    page_object = BaseLoginOneFilePageObject(driver_wrapper)

    # Check instance type, specific locator and common method
    assert isinstance(page_object, IosLoginOneFilePageObject)
    assert page_object.username.locator[1] == 'username_id_ios'
    assert hasattr(page_object, 'login')


def test_mobile_page_object_one_file_android(driver_wrapper):
    driver_wrapper.config.set('Driver', 'type', 'android')
    page_object = BaseLoginOneFilePageObject(driver_wrapper)

    # Check instance type, specific locator and common method
    assert isinstance(page_object, AndroidLoginOneFilePageObject)
    assert page_object.username.locator[1] == 'username_id_android'
    assert hasattr(page_object, 'login')


def test_mobile_page_object_one_file_default(driver_wrapper):
    driver_wrapper.config.set('Driver', 'type', 'unknown')
    page_object = BaseLoginOneFilePageObject(driver_wrapper)

    # Check instance type, specific locator and common method
    assert isinstance(page_object, AndroidLoginOneFilePageObject)
    assert page_object.username.locator[1] == 'username_id_android'
    assert hasattr(page_object, 'login')
