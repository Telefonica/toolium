# -*- coding: utf-8 -*-

u"""
(c) Copyright 2014 Telefónica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefónica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefónica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
"""

import ConfigParser
import io
import os


class ExtendedConfigParser(ConfigParser.ConfigParser):
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
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
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
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return default

    def deepcopy(self):
        """Returns a deep copy of config object

        :returns: a copy of the config object
        """
        # Save actual config to a string
        config_string = io.BytesIO()
        self.write(config_string)

        # We must reset the buffer ready for reading.
        config_string.seek(0)

        # Create a new config object
        config_copy = ExtendedConfigParser()
        config_copy.readfp(config_string)

        return config_copy

    def update_from_system_properties(self):
        """Get defined system properties and update config properties"""
        [self._update_from_system_property(section, option)
         for section in self.sections() for option in self.options(section)]

    def _update_from_system_property(self, section, option):
        """ Update a config property value with system property value
        System property name must be equal to 'Section_option' of config property

        :param section: config section
        :param option: config option
        """
        try:
            property_name = "{0}_{1}".format(section, option)
            self.set(section, option, os.environ[property_name])
        except KeyError:
            pass
