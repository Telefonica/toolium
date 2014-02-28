# -*- coding: utf-8 -*-
'''
(c) Copyright 2014 Telefonica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefonica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefonica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
'''
import logging.config
import ConfigParser
import os
import types


class Config(object):
    def initialize_logger(self):
        '''
        Read logger config file
        '''
        logging.config.fileConfig('conf/logging.conf')

    def initialize_config(self):
        '''
        Create config object with properties file and system properties
        '''
        config = ConfigParser.ConfigParser()
        config.read('conf/properties.cfg')

        # Get system properties and update config properties
        [self._get_system_property(config, section, option)
         for section in config.sections() for option in config.options(section)]

        # Add new methods to config object
        config = self._add_optional_methods(config)

        return config

    def _add_optional_methods(self, config):
        def get_optional(self, section, option, default=None):
            '''
            Get an option value for a given section
            If the section or the option are not found, the default value is returned
            '''
            try:
                return self.get(section, option)
            except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                return default

        def getboolean_optional(self, section, option, default=False):
            '''
            Get an option boolean value for a given section
            If the section or the option are not found, the default value is returned
            '''
            try:
                return self.getboolean(section, option)
            except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                return default

        config.get_optional = types.MethodType(get_optional, config)
        config.getboolean_optional = types.MethodType(getboolean_optional, config)
        return config

    def _get_system_property(self, config, section, option):
        '''
        Update a config property value with system property value
        System property name must be equal to 'Section_option' of config property
        '''
        try:
            property_name = "{0}_{1}".format(section, option)
            config.set(section, option, os.environ[property_name])
        except KeyError:
            pass
