# -*- coding: utf-8 -*-
u"""
Copyright 2016 Telefónica Investigación y Desarrollo, S.A.U.
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


class CommonObject(object):
    """Base class for page objects and page elements

    :type logger: logging.Logger
    :type driver_wrapper: toolium.driver_wrapper.DriverWrapper
    """

    def __init__(self):
        """Initialize common object"""
        self.logger = logging.getLogger(__name__)  #: logger instance
        self.driver_wrapper = None  #: driver wrapper instance

    def reset_object(self):
        """Method to reset this object. This method can be overridden to define specific functionality.
        """
        pass

    @property
    def driver(self):
        """Get driver instance

        :type driver: selenium.webdriver.remote.webdriver.WebDriver or appium.webdriver.webdriver.WebDriver
        :returns: driver instance
        """
        return self.driver_wrapper.driver

    @property
    def config(self):
        """Get config instance

        :type config: toolium.config_parser.ExtendedConfigParser or configparser.ConfigParser
        :returns: config instance
        """
        return self.driver_wrapper.config

    @property
    def utils(self):
        """Get utils instance

        :type utils: toolium.utils.driver_utils.Utils
        :returns: utils instance
        """
        return self.driver_wrapper.utils
