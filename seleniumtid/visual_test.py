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
import os
from seleniumtid import selenium_driver
from types import MethodType
try:
    from needle.engines.perceptualdiff_engine import Engine as diff_Engine
    from needle.engines.pil_engine import Engine as pil_Engine
    from needle.driver import NeedleWebElement
except ImportError:
    pass


class VisualTest(object):
    def __init__(self):
        if not selenium_driver.config.getboolean_optional('Server', 'visualtests_enabled'):
            return

        self.logger = logging.getLogger(__name__)
        self.driver = selenium_driver.driver
        self.output_directory = selenium_driver.output_directory
        self.baseline_directory = selenium_driver.baseline_directory
        engine_type = selenium_driver.config.get_optional('Server', 'visualtests_engine', 'pil')
        self.engine = diff_Engine() if engine_type == 'perceptualdiff' else pil_Engine()
        self.capture = False
        self.save_baseline = selenium_driver.config.getboolean_optional('Server', 'visualtests_save')
        NeedleWebElement.get_dimensions = MethodType(self._get_dimensions.__func__, None, NeedleWebElement)

    def assertScreenshot(self, element_or_selector, filename, file_suffix, threshold=0):
        """
        Assert that a screenshot of an element is the same as a screenshot on disk, within a given threshold.

        :param element_or_selector:
            Either a CSS selector as a string or a WebElement object that represents the element to capture.
        :param filename:
            The filename for the screenshot, which will be appended with ``.png``.
        :param file_suffix:
            A string to be appended to the output filename.
        :param threshold:
            The threshold for triggering a test failure.
        """
        if not selenium_driver.config.getboolean_optional('Server', 'visualtests_enabled'):
            return

        # Search element
        if not isinstance(element_or_selector, NeedleWebElement):
            if element_or_selector.startswith('//'):
                element = self.driver.find_element_by_xpath(element_or_selector)
            else:
                element = self.driver.find_element_by_css_selector(element_or_selector)
        else:
            element = element_or_selector

        baseline_file = os.path.join(self.baseline_directory, '{}.png'.format(filename))
        unique_name = '{0:0=2d}_{1}__{2}.png'.format(selenium_driver.visual_number, filename, file_suffix)
        output_file = os.path.join(self.output_directory, unique_name)

        # Determine whether we should save the baseline image
        if self.save_baseline or not os.path.exists(baseline_file):
            # Save the baseline screenshot and bail out
            element.get_screenshot().save(baseline_file)
            self.logger.debug("Visual screenshot '{}' saved in visualtests/baseline folder".format(filename))
        else:
            # Save the new screenshot
            element.get_screenshot().save(output_file)
            selenium_driver.visual_number += 1
            # Compare the screenshots
            self.engine.assertSameFiles(output_file, baseline_file, threshold)

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
