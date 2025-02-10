# -*- coding: utf-8 -*-
"""
Copyright 2025 Telefónica Investigación y Desarrollo, S.A.U.
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

from configparser import NoSectionError
from toolium.config_driver import ConfigDriver, get_error_message_from_exception


class ConfigDriverPlayWright(ConfigDriver):
    def __init__(self, config, utils=None, playwright=None):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.utils = utils
        self.playwright = playwright

    def create_playwright_browser(self):
        """
        Create a playwright browser using specified config properties

        :returns: a new playwright browser o persistent browser context
        """
        driver_type = self.config.get('Driver', 'type')
        try:
            self.logger.info("Creating playwright driver (type = %s)", driver_type)
            return self._create_playwright_browser()
        except Exception as exc:
            error_message = get_error_message_from_exception(exc)
            self.logger.error("%s driver can not be launched: %s", driver_type.capitalize(), error_message)
            raise

    def create_playwright_persistent_browser_context(self):
        """
        Create a playwright persistent browser context using specified config properties

        :returns: a new playwright persistent browser context
        """
        driver_type = self.config.get('Driver', 'type')
        try:
            self.logger.info("Creating playwright persistent context (type = %s)", driver_type)
            return self._create_playwright_persistent_browser_context()
        except Exception as exc:
            error_message = get_error_message_from_exception(exc)
            self.logger.error("%s driver can not be launched: %s", driver_type.capitalize(), error_message)
            raise

    def _create_playwright_browser(self):
        """Create a browser in local machine using Playwright

        :returns: a new browser Playwright
        """
        driver_name = self.utils.get_driver_name()
        if driver_name in ('android', 'ios', 'iphone'):
            raise Exception('Playwright does not support mobile devices')
        else:
            if driver_name in ['chrome', 'chromium']:
                browser = self._setup_playwright_chrome()
            elif driver_name == 'firefox':
                browser = self._setup_playwright_firefox()
            elif driver_name in ['safari', 'webkit']:
                browser = self._setup_playwright_webkit()
            else:
                raise Exception(f'Playwright does not support {driver_name} driver')
        return browser

    def _create_playwright_persistent_browser_context(self):
        """Create a browser in local machine using Playwright

        :returns: a new persistent browser context Playwright
        """
        driver_name = self.utils.get_driver_name()
        if driver_name in ('android', 'ios', 'iphone'):
            raise Exception('Playwright does not support mobile devices')
        else:
            if driver_name in ['chrome', 'chromium']:
                browser_context = self._setup_playwright_persistent_chrome()
            elif driver_name == 'firefox':
                browser_context = self._setup_playwright_persistent_firefox()
            elif driver_name in ['safari', 'webkit']:
                browser_context = self._setup_playwright_persistent_webkit()
            else:
                raise Exception(f'Playwright does not support {driver_name} driver')
        return browser_context

    def get_playwright_context_options(self):
        """Get Playwright context options from properties file

        :returns: Playwright context options
        """
        context_options = {}
        try:
            for key, value in dict(self.config.items('PlaywrightContextOptions')).items():
                self.logger.debug("Added Playwright context option: %s = %s", key, value)
                context_options[key] = self._convert_property_type(value)
        except NoSectionError:
            pass
        window_width = self.config.get_optional('Driver', 'window_width')
        window_height = self.config.get_optional('Driver', 'window_height')
        if window_width and window_height:
            context_options['viewport'] = {'width': int(window_width), 'height': int(window_height)}
        return context_options

    def get_playwright_page_options(self):
        """Get Playwright page options from properties file

        :returns: Playwright page options
        """
        page_options = {}
        try:
            for key, value in dict(self.config.items('PlaywrightPageOptions')).items():
                self.logger.debug("Added Playwright page option: %s = %s", key, value)
                page_options[key] = self._convert_property_type(value)
        except NoSectionError:
            pass
        return page_options

    def _setup_playwright_firefox(self):
        """Setup Playwright Firefox browser

        :returns: a new Playwright Firefox browser
        """
        headless_mode = self.config.getboolean_optional('Driver', 'headless')
        arguments = []
        preferences = {}
        self._add_playwright_firefox_arguments(arguments)
        # Note: Playwright does not support Firefox extensions
        self._add_playwright_firefox_preferences(preferences)
        browser_options = self._get_playwright_browser_options()
        browser_options = self._update_dict(browser_options, {'args': arguments})
        browser_options = self._update_dict(browser_options, {'firefox_user_prefs': preferences})
        return self.playwright.firefox.launch(
            headless=headless_mode,
            **browser_options
        )

    def _setup_playwright_persistent_firefox(self):
        """Setup Playwright Firefox persistent browser context

        :returns: a new Playwright Firefox persistent browser context
        """
        headless_mode = self.config.getboolean_optional('Driver', 'headless')
        arguments = []
        preferences = {}
        self._add_playwright_firefox_arguments(arguments)
        # Note: Playwright does not support Firefox extensions
        self._add_playwright_firefox_preferences(preferences)
        context_options = self.get_playwright_context_options()
        context_options = self._update_dict(context_options, {'args': arguments})
        context_options = self._update_dict(context_options, {'firefox_user_prefs': preferences})
        return self.playwright.firefox.launch_persistent_context(
            headless=headless_mode,
            **context_options
        )

    def _add_playwright_firefox_arguments(self, arguments):
        """Add Firefox arguments from properties file prepared for Playwright

        :param arguments: Firefox arguments object
        """
        try:
            for pref, pref_value in dict(self.config.items('FirefoxArguments')).items():
                pref_value = '={}'.format(pref_value) if pref_value else ''
                self.logger.debug("Added Firefox argument: %s%s", pref, pref_value)
                arguments.append('--{}{}'.format(pref, self._convert_property_type(pref_value)))
        except NoSectionError:
            pass

    def _add_playwright_firefox_preferences(self, preferences):
        """Add Firefox preferences from properties file prepared for Playwright

        :param preferences: Firefox preferences object
        """
        try:
            for pref, pref_value in dict(self.config.items('FirefoxPreferences')).items():
                self.logger.debug("Added Firefox preference: %s = %s", pref, pref_value)
                preferences[pref] = self._convert_property_type(pref_value)
        except NoSectionError:
            pass

    def _get_playwright_browser_options(self):
        """
        Get Playwright browser options from properties file

        :returns: Playwright browser options
        """
        browser_options = {}
        try:
            for key, value in dict(self.config.items('PlaywrightBrowserOptions')).items():
                self.logger.debug("Added Playwright Browser option: %s = %s", key, value)
                browser_options[key] = self._convert_property_type(value)
        except NoSectionError:
            pass
        return browser_options

    def _setup_playwright_chrome(self):
        """
        Setup Playwright Chrome browser

        :returns: a new Playwright Chrome browser
        """
        headless_mode = self.config.getboolean_optional('Driver', 'headless')
        arguments = []
        self._add_playwright_chrome_arguments(arguments)
        self._add_playwright_chrome_extensions(arguments)
        browser_options = self._get_playwright_browser_options()
        browser_options = self._update_dict(browser_options, {'args': arguments})
        return self.playwright.chromium.launch(
            headless=headless_mode,
            **browser_options
        )

    def _setup_playwright_persistent_chrome(self):
        """
        Setup Playwright Chrome persistent browser context

        :returns: a new Playwright Chrome persistent browser context
        """
        headless_mode = self.config.getboolean_optional('Driver', 'headless')
        arguments = []
        self._add_playwright_chrome_arguments(arguments)
        self._add_playwright_chrome_extensions(arguments)
        context_options = self.get_playwright_context_options()
        context_options = self._update_dict(context_options, {'args': arguments})
        return self.playwright.chromium.launch_persistent_context(
            headless=headless_mode,
            **context_options
        )

    def _add_playwright_chrome_arguments(self, arguments):
        """Add Chrome arguments from properties file prepared for Playwright

        :param arguments: Chrome arguments object
        """
        try:
            for pref, pref_value in dict(self.config.items('ChromeArguments')).items():
                pref_value = '={}'.format(pref_value) if pref_value else ''
                self.logger.debug("Added Chrome argument: %s%s", pref, pref_value)
                arguments.append('--{}{}'.format(pref, self._convert_property_type(pref_value)))
        except NoSectionError:
            pass

    def _add_playwright_chrome_extensions(self, arguments):
        """Add Chrome extensions from properties file

        :param arguments: Chrome options object
        """
        try:
            for pref, pref_value in dict(self.config.items('ChromeExtensions')).items():
                self.logger.debug("Added Chrome extension: %s = %s", pref, pref_value)
                arguments.append('--load-extension={}'.format(pref_value))
        except NoSectionError:
            pass

    def _setup_playwright_webkit(self):
        """Setup Playwright Webkit browser

        :returns: a new Playwright Webkit browser
        """
        headless_mode = self.config.getboolean_optional('Driver', 'headless')
        browser_options = self._get_playwright_browser_options()
        return self.playwright.webkit.launch(
            headless=headless_mode,
            **browser_options
        )

    def _setup_playwright_persistent_webkit(self):
        """Setup Playwright Webkit persistent browser context

        :returns: a new Playwright Webkit persistent browser context
        """
        headless_mode = self.config.getboolean_optional('Driver', 'headless')
        context_options = self.get_playwright_context_options()
        return self.playwright.webkit.launch_persistent_context(
            headless=headless_mode,
            **context_options
        )
