# -*- coding: utf-8 -*-
"""
Copyright 2024 Telefónica Innovación Digital, S.L.
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

from playwright.async_api import Page
from toolium.pageobjects.page_object import PageObject


class PlaywrightPageObject(PageObject):
    """Class to represent a playwright web page"""

    def __init__(self, page: Page):
        """Initialize page object properties

        :param page: playwright page instance
        """
        self.page = page
        super(PlaywrightPageObject, self).__init__()
