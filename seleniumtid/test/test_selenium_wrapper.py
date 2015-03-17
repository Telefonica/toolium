# -*- coding: utf-8 -*-
'''
(c) Copyright 2015 Telefonica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefonica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefonica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
'''
import unittest
from seleniumtid.config_parser import ExtendedConfigParser
from seleniumtid.selenium_wrapper import SeleniumWrapper
from ddt import ddt, data, unpack
import os

mobile_tests = (
    ('android-4.1.2-on-android', True),
    ('android', True),
    ('iphone', True),
    ('firefox-4.1.2-on-android', False),
    ('firefox', False),
)

web_tests = (
    ('android-4.1.2-on-android', 'C:/TestApp.apk', False),
    ('android', 'C:/TestApp.apk', False),
    ('android', 'chrome', True),
    ('android', 'chromium', True),
    ('android', 'browser', True),
    ('iphone', '/tmp/TestApp.zip', False),
    ('iphone', 'safari', True),
    ('firefox-4.1.2-on-android', '', True),
    ('firefox', '', True),
)


@ddt
class SeleniumWrapperTests(unittest.TestCase):
    def setUp(self):
        os.environ["Files_properties"] = 'conf/properties.cfg'
        self.wrapper = SeleniumWrapper()
        self.wrapper.configure_logger()
        self.wrapper.configure_properties()

    def test_singleton(self):
        new_value = 'opera'
        self.wrapper.config.set('Browser', 'browser', new_value)
        new_wrapper = SeleniumWrapper()

        # wrapper and new_wrapper are the same object
        self.assertEquals(new_value, self.wrapper.config.get('Browser', 'browser'))
        self.assertEquals(new_value, new_wrapper.config.get('Browser', 'browser'))
        self.assertEquals(self.wrapper, new_wrapper)

    def test_configure_properties(self):
        os.environ["Files_properties"] = 'conf/properties.cfg'
        self.wrapper.configure_properties()
        self.assertEquals('firefox', self.wrapper.config.get('Browser', 'browser'))  # get last value
        self.assertEquals('5', self.wrapper.config.get_optional('Common', 'implicitly_wait'))  # only in properties
        self.assertEquals(None, self.wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_android(self):
        os.environ["Files_properties"] = 'conf/android-properties.cfg'
        self.wrapper.configure_properties()
        self.assertEquals('android', self.wrapper.config.get('Browser', 'browser'))  # get last value
        self.assertEquals(None, self.wrapper.config.get_optional('Common', 'implicitly_wait'))  # only in properties
        self.assertEquals('http://qacore02/sites/seleniumExamples/ApiDemos-debug.apk',
                          self.wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_two_files(self):
        os.environ["Files_properties"] = 'conf/properties.cfg;conf/android-properties.cfg'
        self.wrapper.configure_properties()
        self.assertEquals('android', self.wrapper.config.get('Browser', 'browser'))  # get last value
        self.assertEquals('5', self.wrapper.config.get_optional('Common', 'implicitly_wait'))  # only in properties
        self.assertEquals('http://qacore02/sites/seleniumExamples/ApiDemos-debug.apk',
                          self.wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_two_files_android_first(self):
        os.environ["Files_properties"] = 'conf/android-properties.cfg;conf/properties.cfg'
        self.wrapper.configure_properties()
        self.assertEquals('firefox', self.wrapper.config.get('Browser', 'browser'))  # get last value
        self.assertEquals('5', self.wrapper.config.get_optional('Common', 'implicitly_wait'))  # only in properties
        self.assertEquals('http://qacore02/sites/seleniumExamples/ApiDemos-debug.apk',
                          self.wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_file_not_found(self):
        os.environ["Files_properties"] = 'conf/notfound-properties.cfg'
        self.assertRaisesRegexp(Exception, 'Properties config file not found', self.wrapper.configure_properties)

    def test_configure_logger_file_not_found(self):
        os.environ["Files_logging"] = 'conf/notfound-properties.cfg'
        self.wrapper.configure_logger()
        self.wrapper.logger.info('No error, default logging configuration')

    @data(*mobile_tests)
    @unpack
    def test_is_mobile_test(self, browser, is_mobile):
        self.wrapper.config.set('Browser', 'browser', browser)
        self.assertEquals(is_mobile, self.wrapper.is_mobile_test())

    @data(*web_tests)
    @unpack
    def test_is_web_test(self, browser, appium_app, is_web):
        self.wrapper.config.set('Browser', 'browser', browser)
        self.wrapper.config.set('AppiumCapabilities', 'app', appium_app)
        self.assertEquals(is_web, self.wrapper.is_web_test())
