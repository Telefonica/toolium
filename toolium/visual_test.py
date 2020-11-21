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

from __future__ import division  # Python 2.7

import datetime
import itertools
import logging
import os
import re
import shutil
from io import BytesIO
from os import path

from selenium.common.exceptions import NoSuchElementException
from six.moves import xrange  # Python 2 and 3 compatibility

from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.utils.path_utils import get_valid_filename, makedirs_safe

try:
    from needle.engines.perceptualdiff_engine import Engine as PerceptualEngine
    from needle.engines.pil_engine import Engine as PilEngine
    from PIL import Image
    from needle.engines.imagemagick_engine import Engine as MagickEngine
except ImportError:
    pass


class VisualTest(object):
    """Visual testing class

    :type driver_wrapper: toolium.driver_wrapper.DriverWrapper
    """
    template_name = 'VisualTestsTemplate.html'  #: name of the report template
    javascript_name = 'VisualTests.js'  #: name of the javascript file
    css_name = 'VisualTests.css'  #: name of the css file
    report_name = 'VisualTests.html'  #: final visual report name
    driver_wrapper = None  #: driver wrapper instance
    results = {'equal': 0, 'diff': 0, 'baseline': 0}  #: dict to save visual assert results
    force = False  #: if True, screenshot is compared even if visual testing is disabled by configuration

    def __init__(self, driver_wrapper=None, force=False):
        self.driver_wrapper = driver_wrapper if driver_wrapper else DriverWrappersPool.get_default_wrapper()
        self.force = force
        if not self.driver_wrapper.config.getboolean_optional('VisualTests', 'enabled') and not self.force:
            return
        if 'PerceptualEngine' not in globals():
            raise Exception('The visual tests are enabled, but needle is not installed')

        self.utils = self.driver_wrapper.utils
        self.logger = logging.getLogger(__name__)
        self.output_directory = DriverWrappersPool.visual_output_directory

        # Update baseline with real platformVersion value
        if '{platformVersion}' in self.driver_wrapper.baseline_name:
            platform_version = self.driver_wrapper.driver.desired_capabilities['platformVersion']
            baseline_name = self.driver_wrapper.baseline_name.replace('{platformVersion}', platform_version)
            self.driver_wrapper.baseline_name = baseline_name
            self.driver_wrapper.visual_baseline_directory = os.path.join(DriverWrappersPool.visual_baseline_directory,
                                                                         get_valid_filename(baseline_name))

        self.baseline_directory = self.driver_wrapper.visual_baseline_directory
        self.engine = self._get_engine()
        self.save_baseline = self.driver_wrapper.config.getboolean_optional('VisualTests', 'save')

        # Create folders
        makedirs_safe(self.baseline_directory)
        makedirs_safe(self.output_directory)

        # Copy js, css and html template to output directory
        dst_template_path = os.path.join(self.output_directory, self.report_name)
        if not os.path.exists(dst_template_path):
            resources_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
            orig_template_path = os.path.join(resources_path, self.template_name)
            orig_javascript_path = os.path.join(resources_path, self.javascript_name)
            dst_javascript_path = os.path.join(self.output_directory, self.javascript_name)
            orig_css_path = os.path.join(resources_path, self.css_name)
            dst_css_path = os.path.join(self.output_directory, self.css_name)
            shutil.copyfile(orig_template_path, dst_template_path)
            shutil.copyfile(orig_javascript_path, dst_javascript_path)
            shutil.copyfile(orig_css_path, dst_css_path)
            self._add_summary_to_report()

    def _get_engine(self):
        """Get configured or default visual engine

        :returns: engine instance
        """
        engine_type = self.driver_wrapper.config.get_optional('VisualTests', 'engine', 'pil')
        if engine_type == 'perceptualdiff':
            engine = PerceptualEngine()
        elif engine_type == 'imagemagick' and 'MagickEngine' not in globals():
            self.logger.warning("Engine '%s' not found, using pil instead. You need needle 0.4+ to use this engine.",
                                engine_type)
            engine = PilEngine()
        elif engine_type == 'imagemagick':
            engine = MagickEngine()
        elif engine_type == 'pil':
            engine = PilEngine()
        else:
            self.logger.warning("Engine '%s' not found, using pil instead. Review your properties.cfg file.",
                                engine_type)
            engine = PilEngine()
        return engine

    def assert_screenshot(self, element, filename, file_suffix=None, threshold=0, exclude_elements=[]):
        """Assert that a screenshot of an element is the same as a screenshot on disk, within a given threshold

        :param element: either a WebElement, PageElement or element locator as a tuple (locator_type, locator_value).
                        If None, a full screenshot is taken.
        :param filename: the filename for the screenshot, which will be appended with ``.png``
        :param file_suffix: a string to be appended to the output filename with extra info about the test.
        :param threshold: percentage threshold for triggering a test failure (value between 0 and 1)
        :param exclude_elements: list of WebElements, PageElements or element locators as a tuple (locator_type,
                                 locator_value) that must be excluded from the assertion
        """
        if not self.driver_wrapper.config.getboolean_optional('VisualTests', 'enabled') and not self.force:
            return
        if not (isinstance(threshold, int) or isinstance(threshold, float)) or threshold < 0 or threshold > 1:
            raise TypeError('Threshold must be a number between 0 and 1: {}'.format(threshold))

        # Search elements
        web_element = self.utils.get_web_element(element)
        exclude_web_elements = []
        for exclude_element in exclude_elements:
            try:
                exclude_web_elements.append(self.utils.get_web_element(exclude_element))
            except NoSuchElementException as e:
                self.logger.warning("Element to be excluded not found: %s", str(e))

        baseline_file = os.path.join(self.baseline_directory, '{}.png'.format(filename))
        filename_with_suffix = '{0}__{1}'.format(filename, file_suffix) if file_suffix else filename
        unique_name = '{0:0=2d}_{1}'.format(DriverWrappersPool.visual_number, filename_with_suffix)
        unique_name = '{}.png'.format(get_valid_filename(unique_name))
        output_file = os.path.join(self.output_directory, unique_name)
        report_name = '{}<br>({})'.format(file_suffix, filename) if file_suffix else '-<br>({})'.format(filename)

        # Get screenshot and modify it
        img = Image.open(BytesIO(self.driver_wrapper.driver.get_screenshot_as_png()))
        img = self.remove_scrolls(img)
        img = self.mobile_resize(img)
        img = self.exclude_elements(img, exclude_web_elements)
        img = self.crop_element(img, web_element)
        img.save(output_file)
        DriverWrappersPool.visual_number += 1

        # Determine whether we should save the baseline image
        if self.save_baseline:
            # Copy screenshot to baseline
            shutil.copyfile(output_file, baseline_file)

            if self.driver_wrapper.config.getboolean_optional('VisualTests', 'complete_report'):
                self._add_result_to_report('baseline', report_name, output_file, None, 'Screenshot added to baseline')

            self.logger.debug("Visual screenshot '%s' saved in visualtests/baseline folder", filename)
        elif not os.path.exists(baseline_file):
            # Baseline should exist if save mode is not enabled
            error_message = "Baseline file not found: %s" % baseline_file
            self.logger.warning(error_message)
            self._add_result_to_report('diff', report_name, output_file, None, 'Baseline file not found')
            if self.driver_wrapper.config.getboolean_optional('VisualTests', 'fail') or self.force:
                raise AssertionError(error_message)
        else:
            # Compare the screenshots
            self.compare_files(report_name, output_file, baseline_file, threshold)

    def get_scrolls_size(self):
        """Return Chrome and Explorer scrolls sizes if they are visible
        Firefox screenshots don't contain scrolls

        :returns: dict with horizontal and vertical scrolls sizes
        """
        scroll_x = 0
        scroll_y = 0
        if self.utils.get_driver_name() in ['chrome', 'iexplore'] and not self.driver_wrapper.is_mobile_test():
            scroll_height = self.driver_wrapper.driver.execute_script("return document.body.scrollHeight")
            scroll_width = self.driver_wrapper.driver.execute_script("return document.body.scrollWidth")
            window_height = self.driver_wrapper.driver.execute_script("return window.innerHeight")
            window_width = self.driver_wrapper.driver.execute_script("return window.innerWidth")
            scroll_size = 21 if self.utils.get_driver_name() == 'iexplore' else 17
            scroll_x = scroll_size if scroll_width > window_width else 0
            scroll_y = scroll_size if scroll_height > window_height else 0
        return {'x': scroll_x, 'y': scroll_y}

    def remove_scrolls(self, img):
        """Remove browser scrolls from image if they are visible

        :param img: image object
        :returns: modified image object
        """
        scrolls_size = self.get_scrolls_size()
        if scrolls_size['x'] > 0 or scrolls_size['y'] > 0:
            new_image_width = img.size[0] - scrolls_size['y']
            new_image_height = img.size[1] - scrolls_size['x']
            img = img.crop((0, 0, new_image_width, new_image_height))
        return img

    def mobile_resize(self, img):
        """Resize image in iOS (native and web) and Android (web) to fit window size

        :param img: image object
        :returns: modified image object
        """
        if self.driver_wrapper.is_ios_test() or self.driver_wrapper.is_android_web_test():
            scale = img.size[0] / self.utils.get_window_size()['width']
            if scale != 1:
                new_image_size = (int(img.size[0] / scale), int(img.size[1] / scale))
                img = img.resize(new_image_size, Image.ANTIALIAS)
        return img

    def get_element_box(self, web_element):
        """Get element coordinates

        :param web_element: WebElement object
        :returns: tuple with element coordinates
        """
        if not self.driver_wrapper.is_mobile_test():
            scroll_x = self.driver_wrapper.driver.execute_script("return window.pageXOffset")
            scroll_x = scroll_x if scroll_x else 0
            scroll_y = self.driver_wrapper.driver.execute_script("return window.pageYOffset")
            scroll_y = scroll_y if scroll_y else 0
            offset_x = -scroll_x
            offset_y = -scroll_y
        else:
            offset_x = 0
            offset_y = self.utils.get_safari_navigation_bar_height()

        location = web_element.location
        size = web_element.size
        return (int(location['x']) + offset_x, int(location['y'] + offset_y),
                int(location['x'] + offset_x + size['width']), int(location['y'] + offset_y + size['height']))

    def crop_element(self, img, web_element):
        """Crop image to fit element

        :param img: image object
        :param web_element: WebElement object
        :returns: modified image object
        """
        if web_element:
            element_box = self.get_element_box(web_element)
            # Reduce element box if it is greater than image size
            element_max_x = img.size[0] if element_box[2] > img.size[0] else element_box[2]
            element_max_y = img.size[1] if element_box[3] > img.size[1] else element_box[3]
            element_box = (element_box[0], element_box[1], element_max_x, element_max_y)
            img = img.crop(element_box)
        return img

    def exclude_elements(self, img, web_elements):
        """Modify image hiding elements with a black rectangle

        :param img: image object
        :param web_elements: WebElement objects to be excluded
        """
        if web_elements and len(web_elements) > 0:
            img = img.convert("RGBA")
            pixel_data = img.load()

            for web_element in web_elements:
                element_box = self.get_element_box(web_element)
                for x, y in itertools.product(xrange(element_box[0], element_box[2]),
                                              xrange(element_box[1], element_box[3])):
                    try:
                        pixel_data[x, y] = (0, 0, 0, 255)
                    except IndexError:
                        pass

        return img

    def compare_files(self, report_name, image_file, baseline_file, threshold):
        """Compare two image files and add result to the html report

        :param report_name: name to show in html report
        :param image_file: image file path
        :param baseline_file: baseline image file path
        :param threshold: percentage threshold
        :returns: error message
        """
        width, height = Image.open(image_file).size
        if isinstance(self.engine, PilEngine):
            # Pil needs a pixel number threshold instead of a percentage threshold
            threshold = int(width * height * threshold)
        try:
            if 'MagickEngine' in globals() and isinstance(self.engine, MagickEngine):
                # Workaround: ImageMagick hangs when images are not equal
                assert (width, height) == Image.open(baseline_file).size, 'Image dimensions do not match'
            self.engine.assertSameFiles(image_file, baseline_file, threshold)
            if self.driver_wrapper.config.getboolean_optional('VisualTests', 'complete_report'):
                self._add_result_to_report('equal', report_name, image_file, baseline_file)
            return None
        except AssertionError as exc:
            diff_message = self._get_diff_message(str(exc), width * height)
            self._add_result_to_report('diff', report_name, image_file, baseline_file, diff_message)
            self.logger.warning("Visual error in '%s': %s", os.path.splitext(os.path.basename(baseline_file))[0],
                                diff_message)
            if self.driver_wrapper.config.getboolean_optional('VisualTests', 'fail') or self.force:
                raise exc
            else:
                return diff_message

    def _add_result_to_report(self, result, report_name, image_file, baseline_file, message=''):
        """Add the result of a visual test to the html report

        :param result: comparation result (equal, diff, baseline)
        :param report_name: name to show in html report
        :param image_file: image file path
        :param baseline_file: baseline image file path
        :param message: error message
        """
        self.results[result] += 1
        row = self._get_html_row(result, report_name, image_file, baseline_file, message)
        self._add_data_to_report_before_tag(row, '</tbody>')
        self._update_report_summary()

    def _add_data_to_report_before_tag(self, data, tag):
        """Add data to visual report before tag

        :param data: data to be added
        :param tag: data will be added before this tag
        """
        with open(os.path.join(self.output_directory, self.report_name), "r+") as f:
            report = f.read()
            index = report.find(tag)
            report = report[:index] + data + report[index:]
            f.seek(0)
            f.write(report)

    def _update_report_summary(self):
        """Update asserts counter in report"""
        new_results = 'Visual asserts</b>: {} ({} failed)'.format(sum(self.results.values()), self.results['diff'])
        with open(os.path.join(self.output_directory, self.report_name), "r+") as f:
            report = f.read()
            report = re.sub(r'Visual asserts</b>: [0-9]* \([0-9]* failed\)', new_results, report)
            f.seek(0)
            f.write(report)

    def _add_summary_to_report(self):
        """Add visual data summary to the html report"""
        summary = '<p><b>Execution date</b>: {}</p>'.format(datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        summary += '<p><b>Baseline name</b>: {}</p>'.format(path.basename(self.baseline_directory))
        summary += '<p><b>Visual asserts</b>: {} ({} failed)</p>'.format(sum(self.results.values()),
                                                                         self.results['diff'])
        self._add_data_to_report_before_tag(summary, '</div>')

    def _get_html_row(self, result, report_name, image_file, baseline_file, message=''):
        """Create the html row with the result of a visual test

        :param result: comparation result (equal, diff, baseline)
        :param report_name: name to show in html report
        :param image_file: image file path
        :param baseline_file: baseline image file path
        :param message: error message
        :returns: str with the html row
        """
        row = '<tr class=' + result + '>'
        row += '<td>' + report_name + '</td>'

        # Create baseline column
        baseline_col = self._get_img_element(baseline_file, 'Baseline image')
        row += '<td>' + baseline_col + '</td>'

        # Create image column
        image_col = self._get_img_element(image_file, 'Screenshot image')
        row += '<td>' + image_col + '</td>'

        # Create diff column
        diff_file = image_file.replace('.png', '.diff.png')
        diff_col = self._get_img_element(diff_file, message) if os.path.exists(diff_file) else message

        row += '<td>' + diff_col + '</td>'
        row += '</tr>'
        return row

    def _get_img_element(self, image_file, image_title):
        """Create an img html element

        :param image_file: filename of the image
        :param image_title: image title
        :returns: str with the img element
        """
        if not image_file:
            return ''
        image_file_path = path.relpath(image_file, self.output_directory).replace('\\', '/')
        return '<img src="{}" title="{}"/>'.format(image_file_path, image_title)

    @staticmethod
    def _get_diff_message(message, image_size):
        """
        Get formatted message with the distance between images

        :param message: original engine message
        :param image_size: number of pixels to convert absolute distances
        :returns: formatted message
        """
        if message is None:
            # Images are equal
            return ''
        elif message == '' or 'Image dimensions do not match' in message:
            # Different sizes in pil (''), perceptualdiff or imagemagick engines
            return 'Image dimensions do not match'

        # Check pil engine message
        m = re.search('\(by a distance of (.*)\)', message)
        if m:
            return 'Distance of %0.8f' % (float(m.group(1)) / image_size)

        # Check perceptualdiff engine message
        m = re.search('([0-9]*) pixels are different', message)
        if m:
            return 'Distance of %0.8f' % (float(m.group(1)) / image_size)

        # Check imagemagick engine message
        m = re.search(':[\r\n](\d*\.?\d*) \((\d*\.?\d*)\) @', message)
        if m:
            return 'Distance of %0.8f' % float(m.group(2))

        return message
