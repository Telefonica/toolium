# -*- coding: utf-8 -*-
"""
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

import importlib

from toolium.driver_wrapper import DriverWrappersPool
from toolium.pageobjects.page_object import PageObject


class MobilePageObject(PageObject):
    def __new__(cls, driver_wrapper=None):
        """Instantiate android or ios page object from base page object depending on driver configuration

        Base, Android and iOS page objects must be defined with following structure:
            FOLDER/base/MODULE_NAME.py
                class BasePAGE_OBJECT_NAME(MobilePageObject)
            FOLDER/android/MODULE_NAME.py
                class AndroidPAGE_OBJECT_NAME(BasePAGE_OBJECT_NAME)
            FOLDER/ios/MODULE_NAME.py
                class IosPAGE_OBJECT_NAME(BasePAGE_OBJECT_NAME)

        :param driver_wrapper: driver wrapper instance
        :returns: android or ios page object instance
        """
        if cls.__name__.startswith('Base'):
            __driver_wrapper = driver_wrapper if driver_wrapper else DriverWrappersPool.get_default_wrapper()
            __os_name = 'ios' if __driver_wrapper.is_ios_test() else 'android'
            __class_name = cls.__name__.replace('Base', __os_name.capitalize())
            try:
                return getattr(importlib.import_module(cls.__module__), __class_name)(__driver_wrapper)
            except AttributeError:
                __module_name = cls.__module__.replace('.base.', '.{}.'.format(__os_name))
                return getattr(importlib.import_module(__module_name), __class_name)(__driver_wrapper)
        else:
            return super(MobilePageObject, cls).__new__(cls)
