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
import logging
from seleniumtid import selenium_driver
from types import MethodType
try:
    from needle.cases import NeedleTestCase
    from needle.engines.perceptualdiff_engine import Engine as diff_Engine
    from needle.engines.pil_engine import Engine as pil_Engine
    from needle.driver import NeedleWebElement
except ImportError:
    pass


class VisualTest(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.driver = selenium_driver.driver
        if selenium_driver.config.getboolean_optional('Server', 'visualtests_enabled'):
            self.output_directory = selenium_driver.output_directory
            self.baseline_directory = selenium_driver.baseline_directory
            engine_type = selenium_driver.config.get_optional('Server', 'visualtests_engine', 'pil')
            self.engine = diff_Engine() if engine_type == 'perceptualdiff' else pil_Engine()
            self.capture = False
            self.save_baseline = selenium_driver.config.getboolean_optional('Server', 'visualtests_save')
            self.compareScreenshot = MethodType(NeedleTestCase.compareScreenshot.__func__, self, VisualTest)  # @UndefinedVariable @IgnorePep8
            self._assertScreenshot = MethodType(NeedleTestCase.assertScreenshot.__func__, self, VisualTest)  # @UndefinedVariable @IgnorePep8
            NeedleWebElement.get_dimensions = MethodType(self._get_dimensions.__func__, None, NeedleWebElement)

    def assertScreenshot(self, element_or_selector, filename_or_file, threshold=0):
        """
        Assert that a screenshot of an element is the same as a screenshot on disk, within a given threshold.

        :param element_or_selector:
            Either a CSS selector as a string or a :py:class:`~needle.driver.NeedleWebElement` object that represents
            the element to capture.
        :param filename_or_file:
            If a string, then assumed to be the filename for the screenshot, which will be appended with ``.png``.
            Otherwise assumed to be a file object for the baseline image.
        :param threshold:
            The threshold for triggering a test failure.
        """
        save_message = "Visual screenshot '{}' saved in visualtests/baseline folder"
        if selenium_driver.config.getboolean_optional('Server', 'visualtests_enabled'):
            try:
                self._assertScreenshot(element_or_selector, filename_or_file, threshold)
            except IOError as exc:
                # If the baseline does not exist, repeat the assert saving the screenshot
                if (not selenium_driver.config.getboolean_optional('Server', 'visualtests_save') and
                        'You might want to re-run this test in baseline-saving mode' in exc.message):
                    self.save_baseline = True
                    self._assertScreenshot(element_or_selector, filename_or_file, threshold)
                    self.logger.debug(save_message.format(filename_or_file))
            if selenium_driver.config.getboolean_optional('Server', 'visualtests_save'):
                self.logger.debug(save_message.format(filename_or_file))

    def _get_dimensions(self):
        '''
        Returns dimensions of a Web Element
        '''
        location = self.location
        size = self.size
        d = dict()
        d['left'] = location['x']
        d['top'] = location['y']
        d['width'] = size['width']
        d['height'] = size['height']
        return d
