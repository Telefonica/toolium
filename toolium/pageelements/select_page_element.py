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

from selenium.webdriver.support.ui import Select as SeleniumSelect

from toolium.pageelements.page_element import PageElement


class Select(PageElement):
    @property
    def option(self):
        return self.select_object.first_selected_option.text

    @option.setter
    def option(self, value):
        self.select_object.select_by_visible_text(value)

    @property
    def select_object(self):
        return SeleniumSelect(self.element())
