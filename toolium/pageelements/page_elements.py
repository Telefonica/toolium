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
from typing import List, Any

from toolium.driver_wrapper import DriverWrappersPool
from toolium.pageelements.button_page_element import Button
from toolium.pageelements.checkbox_page_element import Checkbox
from toolium.pageelements.group_page_element import Group
from toolium.pageelements.input_radio_page_element import InputRadio
from toolium.pageelements.input_text_page_element import InputText
from toolium.pageelements.link_page_element import Link
from toolium.pageelements.page_element import PageElement
from toolium.pageelements.select_page_element import Select
from toolium.pageelements.text_page_element import Text
from toolium.pageobjects.common_object import CommonObject


class PageElements(CommonObject):
    """Class to represent multiple web or mobile page elements

    :type locator: (selenium.webdriver.common.by.By or appium.webdriver.common.mobileby.MobileBy, str)
    :type parent: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
                  or toolium.pageelements.PageElement
                  or (selenium.webdriver.common.by.By or appium.webdriver.common.mobileby.MobileBy, str)
    :type page_element_class: class
    """
    page_element_class = PageElement  #: class of page elements (PageElement, Button...)

    def __init__(self, by, value, parent=None, page_element_class=None, order=None):
        """Initialize the PageElements object with the given locator components.

        If parent is not None, find_elements will be performed over it, instead of
        using the driver's method, so it can find nested elements.

        :param by: locator type
        :param value: locator value
        :param parent: parent element (WebElement, PageElement or locator tuple)
        :param order: index value if the locator returns more than one element
        :param page_element_class: class of page elements (PageElement, Button...)
        :param shadowroot: CSS SELECTOR of JS element where shadowroot tag appears
        """
        super(PageElements, self).__init__()
        self.locator = (by, value)  #: tuple with locator type and locator value
        self.parent = parent  #: element from which to find actual elements
        self.order = order  #: index value if the locator returns more than one element
        self.shadowroot = None  #: Not implemented for PageElements yet
        self.driver_wrapper = DriverWrappersPool.get_default_wrapper()  #: driver wrapper instance
        # update instance element class or use PageElement class
        if page_element_class:
            self.page_element_class = page_element_class
        self._page_elements = []
        self.reset_object(self.driver_wrapper)

    def reset_object(self, driver_wrapper=None):
        """Reset each page element object

        :param driver_wrapper: driver wrapper instance
        """
        if driver_wrapper:
            self.driver_wrapper = driver_wrapper
        for element in self._page_elements:
            element.reset_object(driver_wrapper)
        self._web_elements = []
        self._page_elements = []

    @property
    def web_elements(self):
        """Find multiple WebElements using element locator

        :returns: list of web element objects
        :rtype: list of selenium.webdriver.remote.webelement.WebElement
                or list of appium.webdriver.webelement.WebElement
        """
        if not self._web_elements or not self.config.getboolean_optional('Driver', 'save_web_element'):
            if self.parent:
                self._web_elements = self.utils.get_web_element(self.parent).find_elements(*self.locator)
            else:
                self._web_elements = self.driver.find_elements(*self.locator)
        return self._web_elements

    @property
    def page_elements(self):
        # type: () -> List[Any]
        """Find multiple PageElement using element locator

        :returns: list of page element objects
        :rtype: list of toolium.pageelements.PageElement
        """
        if not self._page_elements or not self.config.getboolean_optional('Driver', 'save_web_element'):
            self._page_elements = []
            for order, web_element in enumerate(self.web_elements):
                # Create multiple PageElement with original locator and order
                page_element = self.page_element_class(self.locator[0], self.locator[1], parent=self.parent,
                                                       order=order)
                page_element.reset_object(self.driver_wrapper)
                page_element._web_element = web_element
                self._page_elements.append(page_element)
        return self._page_elements

    def __len__(self):
        return len(self.page_elements)

    def __getitem__(self, i):
        return self.page_elements[i]

    def __iter__(self):
        return iter(self.page_elements)


class Buttons(PageElements):
    page_element_class = Button


class Checkboxes(PageElements):
    page_element_class = Checkbox


class InputRadios(PageElements):
    page_element_class = InputRadio


class InputTexts(PageElements):
    page_element_class = InputText


class Links(PageElements):
    page_element_class = Link


class Selects(PageElements):
    page_element_class = Select


class Texts(PageElements):
    page_element_class = Text


class Groups(PageElements):
    page_element_class = Group
