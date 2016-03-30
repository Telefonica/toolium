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

import logging

from toolium.driver_wrapper import DriverWrappersPool
from toolium.pageelements.page_element import PageElement
from toolium.pageobjects.page_object import PageObject


class Group(PageObject, PageElement):
    def __init__(self, by, value, parent=None, driver_wrapper=None):
        """Initialize the Group object with the given locator components.

        :param by: locator type
        :param value: locator value
        :param parent: parent element (WebElement, PageElement or locator tuple)
        :param driver_wrapper: driver wrapper instance
        """
        self.logger = logging.getLogger(__name__)
        self.locator = (by, value)  #: tuple with locator type and locator value
        self.parent = parent  #: element from which to find actual elements
        self.driver_wrapper = driver_wrapper if driver_wrapper else DriverWrappersPool.get_default_wrapper()  #: driver wrapper instance
        self._web_element = None
        self.init_page_elements()
        self._update_page_elements(parent=self)

    def reset_object(self):
        """Reset web element object in all page elements"""
        self._web_element = None
        for element in self._get_page_elements():
            element.reset_object()
