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

from selenium.webdriver.common.by import By

from toolium.pageelements import AVAILABLE_PAGEELEMENT_LIST, AVAILABLE_PAGEELEMENTS_LIST
from toolium.spec_files_loader.module_utils import import_class_from_module_path

# Attribute names for PageElements in PageObject Specification File
PAGE_ELEMENT_MODEL_ATTRIBUTE_NAME = u"Name"
PAGE_ELEMENT_MODEL_ATTRIBUTE_LOCATOR_TYPE = u"Locator-Type"
PAGE_ELEMENT_MODEL_ATTRIBUTE_LOCATOR_VALUE = u"Locator-Value"
PAGE_ELEMENT_MODEL_ATTRIBUTE_WAIT = u"Wait-For-Loaded"


class PageElementSpecLoader:
    """
    Implements the logic for loading PageElements based on the configuration read from Specification Files.
    """

    def __init__(self):
        pass

    @staticmethod
    def _get_toolium_page_element_base_class(page_element_class_name):
        """
        Returns the generic base class to be used as parent of the new PageElement.
        If the given PageElement is not defined as a Toolium PageElement, return None
        :param page_element_class_name: PageElement class name
        :return: Toolium PageElement base class or None if not found
        """
        if page_element_class_name in AVAILABLE_PAGEELEMENT_LIST:
            return "PageElementModel"

        if page_element_class_name in AVAILABLE_PAGEELEMENTS_LIST:
            return "PageElementsModel"

    def load_page_element_from_model(self, pageelement_model_data, page_element_class_name, page_element_module):
        """"
        This method returns an instance of the given PageElement located in the Python module specified.

        :param pageelement_model_data: (dict) Attributes loaded for the PageElement from the Specification File
        :param page_element_class_name: (string) Name of the Class for the PageElement
        :param page_element_module: (string) Python module path where the given PageElement class has been implemented
        :return A new instance of the PageElement based on the generic PageElementModel and the given class (parents)
        """

        page_element_base_model_class = self._get_toolium_page_element_base_class(page_element_class_name)
        PageElementModelBaseClass = import_class_from_module_path("toolium.pageelements.page_element_model",
                                                                  page_element_base_model_class)
        PageElementModelSpecImportedClass = import_class_from_module_path(page_element_module,
                                                                          page_element_class_name)
        # PageElement class based on PageElementModelBaseClass and PageElementModelSpecImportedClass parent classes
        PageElementModel = type("PageElementModel",
                                (PageElementModelBaseClass, PageElementModelSpecImportedClass),
                                dict())

        # The name of the class will be name of the PageElement class loaded from Spec File instead of the base class
        PageElementModel.__name__ = page_element_class_name

        # Return an instance of the PageElement
        return PageElementModel(by=getattr(By, pageelement_model_data[PAGE_ELEMENT_MODEL_ATTRIBUTE_LOCATOR_TYPE]),
                                value=pageelement_model_data[PAGE_ELEMENT_MODEL_ATTRIBUTE_LOCATOR_VALUE],
                                wait=pageelement_model_data[PAGE_ELEMENT_MODEL_ATTRIBUTE_WAIT])
