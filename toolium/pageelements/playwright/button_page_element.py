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

from toolium.pageelements.playwright.page_element import PageElement


class Button(PageElement):
    async def get_text(self):
        """Get the element text value

        :returns: element text value
        """
        return await (await self.web_element).get_text()

    async def click(self):
        """Click the element

        :returns: page element instance
        """
        await (await self.web_element).click()
        return self
