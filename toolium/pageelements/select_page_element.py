# -*- coding: utf-8 -*-
"""
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

from selenium.webdriver.support.ui import Select as SeleniumSelect

from toolium.pageelements.page_element import PageElement


class Select(PageElement):
    @property
    def option(self):
        """Return text of the first selected option

        :returns: first selected option text
        """
        return self.selenium_select.first_selected_option.text

    @option.setter
    def option(self, value):
        """Select option by text

        :param value: new option value
        """
        self.selenium_select.select_by_visible_text(value)

    @property
    def selenium_select(self):
        """Return Selenium select object to call other select methods, like select_by_index, deselect_by_index...

        :returns: Selenium select object
        """
        return SeleniumSelect(self.web_element)
