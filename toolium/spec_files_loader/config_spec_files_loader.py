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

import logging
import os

from yaml import load

from toolium.spec_files_loader.page_object_spec_loader import PageObjectSpecLoader


class ConfigSpecFilesLoader(object):
    """
    This Loader builds all PageObject from the information given in PageObject Specification Files (YAML files).
        - Builds all PageObjects with the given PageElements and its configuration.
        - Build PageElements already existing in Toolium.
        - TODO: Allow to include in the PageObject Models all PageElements implemented by the user.
        - TODO: Allow to inherit already implemented PageObjects by the user.

    Toolium Configuration required:
        [PageObjectSpecFiles]
        enabled: true
        spec_files_path: resources/pageobject_spec_files
        custom_page_object_module_path: common/pageobjects
        custom_page_elements_module_path: common/pageelements
    """

    def __init__(self, config):
        """
        Configure the SpecFile Loader
        :param config: Toolium configuration
        """
        self.logger = logging.getLogger(__name__)
        self.config = config.deepcopy()
        self.loaded_page_object_models = dict()
        self.page_object_loader = PageObjectSpecLoader()

    def load_page_object_definition(self):
        """
        Loads the Specification Files as YAML documents containing the definition of all PageObjects
        and its PageElements.
        PageObjets are not created but only the configuration is loaded.
        """

        if not self.config.getboolean_optional("PageObjectSpecFiles", "enabled", False):
            self.logger.warn("PageObject Specification Files loader is disabled by Toolium configuration")
            return None

        self.logger.info("Loading PageObjects from YAML Specification Files")

        yaml_path = self.config.get_optional("PageObjectSpecFiles",
                                             "spec_files_path",
                                             "resources/pageobject_spec_files")
        self.logger.debug("Location to look for PageObject Specification Files: '%s'", yaml_path)

        custom_pageelements_path = self.config.get_optional("PageObjectSpecFiles",
                                                            "custom_page_elements_module_path",
                                                            "common/pageelements")
        self.logger.debug("Path to look for custom PageElements: '%s'", custom_pageelements_path)

        custom_pageobjects_path = self.config.get_optional("PageObjectSpecFiles",
                                                           "custom_page_object_module_path",
                                                           "common/pageobjects")
        self.logger.debug("Path to look for custom PageObjects: '%s'", custom_pageobjects_path)

        definition_file_list = list()
        if os.path.isfile(yaml_path):
            definition_file_list.append(yaml_path)
        else:
            for root, dirs, aux_definition_files in os.walk(yaml_path, topdown=False):
                definition_file_list += [os.path.join(root, definition_file) for definition_file in aux_definition_files
                                         if ".yml" or ".yaml" in definition_file]

        if not definition_file_list:
            self.logger.warn("No models loaded. Has been the spec files path properly configured? '%s'", yaml_path)
        else:
            for definition_file in definition_file_list:
                with open(definition_file, 'r') as stream:
                    self.loaded_page_object_models.update(load(stream))
            self.logger.debug("Loaded data: %s", self.loaded_page_object_models)

    def init_page_object(self, page_object_name):
        """
        Creates a new PageObject based on the specification loaded from YAML file.
        :param page_object_name: (string) name of the required PageObject to be initialized
        :return: PageObject instance properly built with all the defined PageElements.
        """

        if not self.config.getboolean_optional("PageObjectSpecFiles", "enabled", False):
            raise Exception("You are trying to use the PageObject Specification Files Loader, "
                            "but it is disabled by Toolium configuration")

        found_page_object_model_data = None
        for page_object in self.loaded_page_object_models:
            if page_object == page_object_name:
                found_page_object_model_data = self.loaded_page_object_models[page_object]
                break

        if not found_page_object_model_data:
            raise Exception("Page object %s not found in the loaded Specification Files" % page_object_name)

        return self.page_object_loader.load_page_object_from_model(page_object_name, found_page_object_model_data)
