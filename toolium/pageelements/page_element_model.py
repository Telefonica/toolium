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

from toolium.pageelements import PageElement, PageElements


class PageElementModel(PageElement):
    """
    Class to represent a PageElement when it is defined in a PageObject Specification File.
    The PageElementModel instance is built dynamically in runtime based on the specification given in the YAML file.
    """

    def __init__(self, by, value, wait=False):
        """
        Initialize the PageElement object with the given locator loaded from the PageObject Specification File

        :param by: locator type
        :param value: locator value
        :param wait: True if the page element must be loaded in wait_until_loaded method of the container page object
        """
        super(PageElementModel, self).__init__(by, value, wait=wait)
        self.custom_attributes = dict()


class PageElementsModel(PageElements):
    """
    Class to represent a PageElements when it is defined in a PageObject Specification File.
    The PageElementModel instance is built dynamically in runtime based on the specification given in the YAML file.

    :type wait: (bool) whether to wait for each PageElement located by the PageElements definition
    :type custom_attributes: (dict) Additional custom attributes loaded from the specification file.
    """

    def __init__(self, by, value, wait=False):
        """
        Initialize the PageElements object with the given locator loaded from the PageObject Specification File

        :param by: locator type
        :param value: locator value
        :param wait: True if PageElements should wait for each located PageElement or not
        """
        super(PageElementsModel, self).__init__(by, value)
        self.wait = wait  # TODO PageElements -> Wait for all PageElements to be displayed ?
        self.custom_attributes = dict()
