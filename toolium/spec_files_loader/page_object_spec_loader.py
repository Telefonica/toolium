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

from toolium.spec_files_loader.module_utils import import_class_from_module_path
from toolium.spec_files_loader.page_element_spec_loader import PageElementSpecLoader, PAGE_ELEMENT_MODEL_ATTRIBUTE_NAME

# Attribute names for PageElements in PageObject Specification File
PAGE_OBJECT_MODEL_PROPERTIES = u'_Properties_'
PAGE_OBJECT_MODEL_PROPERTIES_BASE_OBJECT = u"BaseObject"


class PageObjectSpecLoader:
    """
    Implements the logic for loading PageObjects based on the configuration read from Specification Files.
    """

    def __init__(self):
        self.pagelement_loader = PageElementSpecLoader()

    def load_page_object_from_model(self, pageobject_name, pageobject_model_data):
        """
        This method returns an instance of the given PageObject with all defined configuration in the Specification File

        :param pageobject_name: (string) Name of the PageObject
        :param pageobject_model_data: (list) List of elements and _Properties_ (if given).
                                      All Specifications to build the PageObject based in the Specification File..
                                      Example:
                                        {
                                         'Text':{
                                           'Locator-Value': 'd0f81d3c',
                                           'Locator-Type': 'ID',
                                           'Name': 'form',
                                           'Wait-For-Loaded': True
                                          }
                                        }
        :return: A new PageObject instance with all the defined PageElements in the Specification File.
        """

        # Load PageObject
        PageObjectModelBaseClass = import_class_from_module_path("toolium.pageobjects.page_object_model",
                                                                 "PageObjectModel")
        # PageObject class based on PageObjectModelBaseClass
        PageObjectModelClass = type("PageObjectModel",
                                    (PageObjectModelBaseClass,),
                                    dict())

        # The name of the class will be name of the PageObject class loaded from Spec File instead of the base class
        PageObjectModelClass.__name__ = pageobject_name
        created_page_object = PageObjectModelClass(page_name=pageobject_name)

        for page_element_data in pageobject_model_data:
            # Data example:
            # page_element_data
            if PAGE_OBJECT_MODEL_PROPERTIES_BASE_OBJECT not in page_element_data:
                page_element_name = list(page_element_data.keys())[0]
                page_element_model_data = list(page_element_data.values())[0]

                page_element_loaded = self.pagelement_loader.load_page_element_from_model(page_element_model_data,
                                                                                          page_element_name,
                                                                                          "toolium.pageelements")
                setattr(created_page_object,
                        page_element_model_data[PAGE_ELEMENT_MODEL_ATTRIBUTE_NAME],
                        page_element_loaded)

        return created_page_object
