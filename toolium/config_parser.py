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

# Python 2 and 3 compatibility
from six.moves import configparser, StringIO


class ExtendedConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        """Override default optionxform in ConfigParser"""
        return optionstr

    def get_optional(self, section, option, default=None):
        """ Get an option value for a given section
        If the section or the option are not found, the default value is returned

        :param section: config section
        :param option: config option
        :param default: default value
        :returns: config value
        """
        try:
            return self.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def getboolean_optional(self, section, option, default=False):
        """ Get an option boolean value for a given section
        If the section or the option are not found, the default value is returned

        :param section: config section
        :param option: config option
        :param default: default value
        :returns: boolean config value
        """
        try:
            return self.getboolean(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def deepcopy(self):
        """Returns a deep copy of config object

        :returns: a copy of the config object
        """
        # Save actual config to a string
        config_string = StringIO()
        self.write(config_string)

        # We must reset the buffer ready for reading.
        config_string.seek(0)

        # Create a new config object
        config_copy = ExtendedConfigParser()
        config_copy.readfp(config_string)

        return config_copy

    def update_from_system_properties(self):
        """Get defined system properties and update config properties"""
        [self._update_property_from_dict(section, option, os.environ)
         for section in self.sections() for option in self.options(section)]

    def update_from_behave_properties(self, behave_properties):
        """Get behave userdata properties and update config properties

        :param behave_properties: behave properties
        """
        [self._update_property_from_dict(section, option, behave_properties)
         for section in self.sections() for option in self.options(section)]

    def _update_property_from_dict(self, section, option, new_properties):
        """ Update a config property value with a new property value
        Property name must be equal to 'Section_option' of config property

        :param section: config section
        :param option: config option
        :param new_properties: dict with new properties values
        """
        try:
            property_name = "{0}_{1}".format(section, option)
            self.set(section, option, new_properties[property_name])
        except KeyError:
            pass

    def _update_from_behave_property(self, section, option, userdata):
        """ Update a config property value with behave userdata property value
        System property name must be equal to 'Section_option' of config property

        :param section: config section
        :param option: config option
        :param userdata: behave userdata properties object
        """
        try:
            property_name = "{0}_{1}".format(section, option)
            self.set(section, option, userdata[property_name])
        except KeyError:
            pass

    @staticmethod
    def get_config_from_file(conf_properties_files):
        """Reads properties files and saves them to a config object

        :param conf_properties_files: comma-separated list of properties files
        :returns: config object
        """
        # Initialize the config object
        config = ExtendedConfigParser()
        logger = logging.getLogger(__name__)

        # Configure properties (last files could override properties)
        found = False
        files_list = conf_properties_files.split(';')
        for conf_properties_file in files_list:
            result = config.read(conf_properties_file)
            if len(result) == 0:
                message = 'Properties config file not found: {}'.format(conf_properties_file)
                if len(files_list) == 1:
                    logger.error(message)
                    raise Exception(message)
                else:
                    logger.warn('Properties config file not found: {}'.format(conf_properties_file))
            else:
                logger.debug('Reading properties from file: {}'.format(conf_properties_file))
                found = True
        if not found:
            message = 'Any of the properties config files has been found'
            logger.error(message)
            raise Exception(message)

        return config
