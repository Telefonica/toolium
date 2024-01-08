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

import logging
import re
from configparser import ConfigParser, NoSectionError, NoOptionError
from io import StringIO

logger = logging.getLogger(__name__)


SPECIAL_SYSTEM_PROPERTIES = ['TOOLIUM_CONFIG_ENVIRONMENT', 'TOOLIUM_OUTPUT_DIRECTORY', 'TOOLIUM_OUTPUT_LOG_FILENAME',
                             'TOOLIUM_CONFIG_DIRECTORY', 'TOOLIUM_CONFIG_LOG_FILENAME',
                             'TOOLIUM_CONFIG_PROPERTIES_FILENAMES', 'TOOLIUM_VISUAL_BASELINE_DIRECTORY']


class ExtendedConfigParser(ConfigParser):
    def optionxform(self, optionstr):
        """Override default optionxform in ConfigParser to allow case sensitive options"""
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
        except (NoSectionError, NoOptionError):
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
        except (NoSectionError, NoOptionError):
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
        config_copy.read_file(config_string)

        return config_copy

    def update_properties(self, new_properties):
        """ Update config properties values
        Property name must be equal to 'Section_option' of config property

        :param new_properties: dict with new properties values
        """
        [self._update_property_from_dict(section, option, new_properties)
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

    def update_toolium_system_properties(self, new_properties):
        """ Update config properties values or add new values if property does not exist
        Property name must be 'TOOLIUM_[SECTION]_[OPTION]' and property value must be '[Section]_[option]=value'
        i.e. TOOLIUM_SERVER_ENABLED='Server_enabled=true'

        Section and option can not be configured in property name because they must be case sensitive and, in Windows,
        system properties are case insensitive

        :param new_properties: dict with new properties values
        """
        for property_name, property_value in new_properties.items():
            name_groups = re.match('^TOOLIUM_([^_]+)_(.+)$', property_name)
            value_groups = re.match('^([^_=]+)_([^=]+)=(.*)$', property_value)
            if (name_groups and value_groups
                    and name_groups.group(1).upper() == value_groups.group(1).upper()
                    and name_groups.group(2).upper() == value_groups.group(2).upper()):
                section = value_groups.group(1)
                option = value_groups.group(2)
                value = value_groups.group(3)
                if not self.has_section(section):
                    self.add_section(section)
                self.set(section, option, value)
            elif property_name.startswith('TOOLIUM') and property_name not in SPECIAL_SYSTEM_PROPERTIES:
                logger.warning('A toolium system property is configured but its name does not math with section'
                               ' and option in value (use TOOLIUM_[SECTION]_[OPTION]=[Section]_[option]=value):'
                               ' %s=%s', property_name, property_value)

    def translate_config_variables(self, str_with_variables):
        """
        Translate config variables included in string with format {Section_option}
        :param context: behave context
        :param str_with_variables: string with config variables, i.e. {Driver_type}_{Driver_width}
        :return: string with translated variables
        """
        for section in self.sections():
            for option in self.options(section):
                option_value = self.get(section, option)
                str_with_variables = str_with_variables.replace('{{{0}_{1}}}'.format(section, option), option_value)
        return str_with_variables

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
                message = 'Properties config file not found: %s'
                if len(files_list) == 1:
                    logger.error(message, conf_properties_file)
                    raise Exception(message % conf_properties_file)
                else:
                    logger.debug(message, conf_properties_file)
            else:
                logger.debug('Reading properties from file: %s', conf_properties_file)
                found = True
        if not found:
            message = 'Any of the properties config files has been found'
            logger.error(message)
            raise Exception(message)

        return config

    # Overwrite ConfigParser methods to allow colon in options names
    # To set a config property with colon in name
    #    selenoid:options = "{'enableVideo': True}"
    # configure properties.cfg with:
    #    selenoid___options: {'enableVideo': True}

    def _encode_option(self, option):
        return option.replace(':', '___')

    def _decode_option(self, option):
        return option.replace('___', ':')

    def get(self, section, option, *args, **kwargs):
        return super().get(section, self._encode_option(option), *args, **kwargs)

    def set(self, section, option, *args):
        super().set(section, self._encode_option(option), *args)

    def options(self, section):
        return [self._decode_option(option) for option in super().options(section)]

    def has_option(self, section, option):
        return super().has_option(section, self._encode_option(option))

    def remove_option(self, section, option):
        return super().remove_option(section, self._encode_option(option))

    def items(self, *args):
        return [(self._decode_option(item[0]), item[1]) for item in super().items(*args)]
