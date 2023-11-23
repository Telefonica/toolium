# -*- coding: utf-8 -*-
"""
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
    native_context = "NATIVE_APP"
    webview_context_prefix = "WEBVIEW"

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

    def _switch_to_new_context(self, context):
        """ Change to a new context if its different than the current one"""
        if self.driver.context != context:
            self.driver.switch_to.context(context)

    def _android_automatic_context_selection(self):
        """Change context selection depending if the element is a webview for android devices"""
        # we choose the appPackage webview context, and select the first window returned by mobile: getContexts
        if self.webview or (self.parent and self.parent.webview):
            context = None
            window_handle = None
            if self.webview_context_selection_callback:
                context, window_handle = self.webview_context_selection_callback(*self.webview_csc_args)
            elif self.parent and self.parent.webview_context_selection_callback:
                context, window_handle = self.parent.webview_context_selection_callback(*self.parent.webview_csc_args)
            else:
                app_web_context = "{}_{}".format(CommonObject.webview_context_prefix,
                                                 self.driver.capabilities['appPackage'])
                if app_web_context in self.driver.contexts:
                    context = app_web_context
                    self._switch_to_new_context(context)
                    window_handle = self.driver.window_handles[0]
                else:
                    raise KeyError("WEBVIEW context not found")

            if context:
                self._switch_to_new_context(context)
                if self.driver.current_window_handle != window_handle:
                    self.driver.switch_to.window(window_handle)
            else:
                raise KeyError("WEBVIEW context not found")
        else:
            self._switch_to_new_context(CommonObject.native_context)

    def _ios_automatic_context_selection(self):
        """Change context selection depending if the element is a webview for ios devices"""
        # we choose the last webview context returned by mobile: getContexts for the bundleid
        if self.webview:
            if self.webview_context_selection_callback:
                context_id = self.webview_context_selection_callback(*self.webview_csc_args)
            else:
                contexts = self.driver.execute_script('mobile: getContexts')
                context_id = next(
                    (item['id'] for item in reversed(contexts) if
                     'bundleId' in item and item['bundleId'] == self.driver.capabilities['bundleId']),
                    None)
            if context_id:
                self._switch_to_new_context(context_id)
            else:
                raise KeyError("WEBVIEW context not found")
        else:
            self._switch_to_new_context(CommonObject.native_context)
