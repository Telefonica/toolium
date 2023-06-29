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

import inspect
import mock
import os
import pytest
import re
import shutil
from PIL import Image

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrapper import DriverWrappersPool
from toolium.test.utils.test_driver_utils import get_mock_element
from toolium.utils.path_utils import makedirs_safe
from toolium.visual_test import VisualTest

# Original file paths
root_path = os.path.dirname(os.path.realpath(__file__))
orig_file_v1 = os.path.join(root_path, 'resources', 'register.png')
orig_file_v2 = os.path.join(root_path, 'resources', 'register_v2.png')
orig_file_v2_diff = os.path.join(root_path, 'resources', 'register_v2_diff.png')
orig_file_small = os.path.join(root_path, 'resources', 'register_small.png')
orig_file_scroll = os.path.join(root_path, 'resources', 'register_chrome_scroll.png')
orig_file_cropped = os.path.join(root_path, 'resources', 'register_cropped_element.png')
orig_file_ios = os.path.join(root_path, 'resources', 'ios.png')
orig_file_ios_web = os.path.join(root_path, 'resources', 'ios_web.png')
orig_file_mac = os.path.join(root_path, 'resources', 'mac_os_retina.png')

# Baseline file paths
baselines_path = os.path.join(root_path, 'output', 'visualtests', 'baseline', 'firefox')
file_v1 = os.path.join(baselines_path, 'register.png')
file_v2 = os.path.join(baselines_path, 'register_v2.png')
file_v2_diff = os.path.join(baselines_path, 'register_v2_diff.png')
file_small = os.path.join(baselines_path, 'register_small.png')
file_scroll = os.path.join(baselines_path, 'register_chrome_scroll.png')
file_cropped = os.path.join(baselines_path, 'register_cropped_element.png')
file_ios = os.path.join(baselines_path, 'ios.png')
file_ios_web = os.path.join(baselines_path, 'ios_web.png')
file_mac = os.path.join(baselines_path, 'mac_os_retina.png')


@pytest.fixture(scope='module', autouse=True)
def initiliaze_files():
    # Remove previous visual path
    visual_path = os.path.join(root_path, 'output', 'visualtests')
    if os.path.exists(visual_path):
        shutil.rmtree(visual_path)

    # Copy files to baseline folder
    makedirs_safe(baselines_path)
    shutil.copyfile(orig_file_v1, file_v1)
    shutil.copyfile(orig_file_v2, file_v2)
    shutil.copyfile(orig_file_v2_diff, file_v2_diff)
    shutil.copyfile(orig_file_small, file_small)
    shutil.copyfile(orig_file_scroll, file_scroll)
    shutil.copyfile(orig_file_cropped, file_cropped)
    shutil.copyfile(orig_file_ios, file_ios)
    shutil.copyfile(orig_file_ios_web, file_ios_web)
    shutil.copyfile(orig_file_mac, file_mac)

    return True


@pytest.fixture
def driver_wrapper():
    # Reset wrappers pool values
    DriverWrappersPool._empty_pool()
    DriverWrapper.config_properties_filenames = None

    # Create a new wrapper
    driver_wrapper = DriverWrappersPool.get_default_wrapper()
    driver_wrapper.utils.get_window_size = mock.MagicMock()
    driver_wrapper.driver = mock.MagicMock()

    # Configure properties
    root_path = os.path.dirname(os.path.realpath(__file__))
    visual_path = os.path.join(root_path, 'output', 'visualtests')
    config_files = ConfigFiles()
    config_files.set_config_directory(os.path.join(root_path, 'conf'))
    config_files.set_config_properties_filenames('properties.cfg')
    config_files.set_output_directory(os.path.join(root_path, 'output'))
    driver_wrapper.configure(config_files)
    driver_wrapper.config.set('VisualTests', 'enabled', 'true')
    DriverWrappersPool.visual_output_directory = os.path.join(visual_path, 'execution')

    yield driver_wrapper

    # Reset wrappers pool values
    DriverWrappersPool._empty_pool()
    DriverWrapper.config_properties_filenames = None


def assert_image(visual, img, img_name, expected_image_filename, expected_result='equal', threshold=0):
    """Save img in an image file and compare with the expected image

    :param img: image object
    :param img_name: temporary filename
    :param expected_image_filename: filename of the expected image
    :param expected_result: expected result
    :param threshold: allowed threshold
    """
    # Save result image in output folder
    result_file = os.path.join(visual.output_directory, f'{img_name}.png')
    img.save(result_file)

    # Output image and expected image must be equal
    expected_image = os.path.join(root_path, 'resources', f'{expected_image_filename}.png')
    compare_image_files(visual, previous_method_name(), result_file, expected_image, expected_result, threshold)


def compare_image_files(visual, report_name, image, expected_image, expected_result='equal', threshold=0):
    """Compare two images

    :param visual: visual testing object
    :param report_name: report name
    :param image: file path image to compare
    :param expected_image: expected image
    :param expected_result: expected result
    :param threshold: allowed threshold
    """
    assert visual.compare_files(report_name, image, expected_image, threshold) == expected_result


def current_method_name():
    """Get current method name

    :returns: the name of the method that has called it
    """
    return inspect.currentframe().f_back.f_code.co_name


def previous_method_name():
    """Get previous method name

    :returns: the name of the method that has called the previous method
    """
    return inspect.currentframe().f_back.f_back.f_code.co_name


def test_no_enabled(driver_wrapper):
    # Update conf and create a new VisualTest instance
    driver_wrapper.config.set('VisualTests', 'enabled', 'false')
    visual = VisualTest(driver_wrapper)

    visual.assert_screenshot(None, filename='screenshot_full', file_suffix=current_method_name())
    driver_wrapper.driver.save_screenshot.assert_not_called()


def test_compare_files_equal(driver_wrapper):
    visual = VisualTest(driver_wrapper)
    assert visual.compare_files(current_method_name(), file_v1, file_v1, 0) == 'equal'


def test_compare_files_diff(driver_wrapper):
    visual = VisualTest(driver_wrapper)
    expected_result = 'diff-Distance is 0.00520373, more than 0 threshold'
    assert visual.compare_files(current_method_name(), file_v2, file_v1, 0) == expected_result


def test_compare_files_similar(driver_wrapper):
    visual = VisualTest(driver_wrapper)
    expected_result = 'equal-Distance is 0.00520373, less than 0.01 threshold'
    assert visual.compare_files(current_method_name(), file_v2, file_v1, 0.01) == expected_result


def test_compare_files_diff_with_threshold(driver_wrapper):
    visual = VisualTest(driver_wrapper)
    expected_result = 'diff-Distance is 0.00520373, more than 0.005 threshold'
    assert visual.compare_files(current_method_name(), file_v2, file_v1, 0.005) == expected_result


def test_compare_files_diff_fail(driver_wrapper):
    # Update conf and create a new VisualTest instance
    driver_wrapper.config.set('VisualTests', 'fail', 'true')
    visual = VisualTest(driver_wrapper)

    with pytest.raises(AssertionError) as exc:
        visual.compare_files(current_method_name(), file_v2, file_v1, 0)
    assert str(exc.value) == f"The new screenshot '{file_v2}' did not match the baseline '{file_v1}' " \
                             f"(by a distance of 0.00520373, more than 0 threshold)"


def test_compare_files_diff_fail_with_threshold(driver_wrapper):
    # Update conf and create a new VisualTest instance
    driver_wrapper.config.set('VisualTests', 'fail', 'true')
    visual = VisualTest(driver_wrapper)

    with pytest.raises(AssertionError) as exc:
        visual.compare_files(current_method_name(), file_v2, file_v1, 0.005)
    assert str(exc.value) == f"The new screenshot '{file_v2}' did not match the baseline '{file_v1}' " \
                             f"(by a distance of 0.00520373, more than 0.005 threshold)"


def test_compare_files_size(driver_wrapper):
    visual = VisualTest(driver_wrapper)
    expected_result = 'diff-Image dimensions (1446, 378) do not match baseline size (1680, 388)'
    assert visual.compare_files(current_method_name(), file_small, file_v1, 0) == expected_result


def test_compare_files_size_fail(driver_wrapper):
    # Update conf and create a new VisualTest instance
    driver_wrapper.config.set('VisualTests', 'fail', 'true')
    visual = VisualTest(driver_wrapper)

    with pytest.raises(AssertionError) as exc:
        visual.compare_files(current_method_name(), file_small, file_v1, 0)
    assert str(exc.value) == f"The new screenshot '{file_small}' size '(1446, 378)' did not match the baseline" \
                             f" '{file_v1}' size '(1680, 388)'"


def test_get_img_element(driver_wrapper):
    expected_img = r'<img src=".*register_v2.png" title="Baseline image"/>'
    visual = VisualTest(driver_wrapper)
    img = visual._get_img_element('register_v2.png', 'Baseline image')
    assert re.compile(expected_img).match(img) is not None


def test_get_html_row(driver_wrapper):
    expected_row = r'<tr class=diff><td>report_name</td><td><img src=".*register_v2.png" title="Baseline image"/>' \
                   r'</td><td><img src=".*register.png" title="Screenshot image"/></td><td></td></tr>'
    visual = VisualTest(driver_wrapper)
    row = visual._get_html_row('diff', 'report_name', file_v1, file_v2, None, None)
    assert re.compile(expected_row).match(row) is not None


def test_get_html_row_message(driver_wrapper):
    result_message = 'Distance is 0.00520373, more than 0 threshold'
    expected_row = r'<tr class=diff><td>report_name</td><td><img src=".*register_v2.png" title="Baseline image"/>' \
                   f'</td><td><img src=".*register.png" title="Screenshot image"/></td><td>{result_message}</td></tr>'
    visual = VisualTest(driver_wrapper)
    row = visual._get_html_row('diff', 'report_name', file_v1, file_v2, None, result_message)
    assert re.compile(expected_row).match(row) is not None


def test_get_html_row_with_diff_image(driver_wrapper):
    result_message = 'Distance is 0.00520373, more than 0 threshold'
    expected_row = r'<tr class=diff><td>report_name</td><td><img src=".*register_v2.png" title="Baseline image"/>' \
                   r'</td><td><img src=".*register.png" title="Screenshot image"/></td>' \
                   f'<td><img src=".*register_v2.diff.png" title="{result_message}"/></td></tr>'
    visual = VisualTest(driver_wrapper)
    row = visual._get_html_row('diff', 'report_name', file_v1, file_v2, file_v2_diff, result_message)
    assert re.compile(expected_row).match(row) is not None


def test_crop_element(driver_wrapper):
    # Create element mock
    driver_wrapper.driver.execute_script.return_value = 0  # scrollX=0 and scrollY=0
    web_element = get_mock_element(x=250, y=40, height=40, width=300)
    visual = VisualTest(driver_wrapper)

    # Resize image
    img = Image.open(file_v1)
    img = visual.crop_element(img, web_element)

    # Assert output image
    assert_image(visual, img, current_method_name(), 'register_cropped_element')


def test_crop_element_oversize(driver_wrapper):
    # Create element mock
    driver_wrapper.driver.execute_script.return_value = 0  # scrollX=0 and scrollY=0
    web_element = get_mock_element(x=250, y=200, height=400, width=300)
    # y + width > img.size[1] --> 600 > 388
    visual = VisualTest(driver_wrapper)

    # Resize image
    img = Image.open(file_v1)
    img = visual.crop_element(img, web_element)

    # Assert output image
    assert_image(visual, img, current_method_name(), 'register_cropped_element_oversize')


def test_get_scrolls_size(driver_wrapper):
    # Update conf and create a new VisualTest instance
    # Mock scrollHeight, scrollWidth, innerHeight, innerWidth
    driver_wrapper.driver.execute_script.side_effect = [600, 1200, 400, 900]
    driver_wrapper.config.set('Driver', 'type', 'chrome')
    visual = VisualTest(driver_wrapper)

    # Check scrolls
    assert visual.get_scrolls_size() == {'x': 17, 'y': 17}


def test_get_scrolls_size_y(driver_wrapper):
    # Update conf and create a new VisualTest instance
    # Mock scrollHeight, scrollWidth, innerHeight, innerWidth
    driver_wrapper.driver.execute_script.side_effect = [600, 1200, 400, 1200]
    driver_wrapper.config.set('Driver', 'type', 'chrome')
    visual = VisualTest(driver_wrapper)

    # Check scrolls
    assert visual.get_scrolls_size() == {'x': 0, 'y': 17}


def test_get_scrolls_size_without_scrolls(driver_wrapper):
    # Update conf and create a new VisualTest instance
    # Mock scrollHeight, scrollWidth, innerHeight, innerWidth
    driver_wrapper.driver.execute_script.side_effect = [600, 1200, 600, 1200]
    driver_wrapper.config.set('Driver', 'type', 'chrome')
    visual = VisualTest(driver_wrapper)

    # Check scrolls
    assert visual.get_scrolls_size() == {'x': 0, 'y': 0}


def test_get_scrolls_size_iexplore(driver_wrapper):
    # Update conf and create a new VisualTest instance
    # Mock scrollHeight, scrollWidth, innerHeight, innerWidth
    driver_wrapper.driver.execute_script.side_effect = [600, 1200, 400, 900]
    driver_wrapper.config.set('Driver', 'type', 'iexplore')
    visual = VisualTest(driver_wrapper)

    # Check scrolls
    assert visual.get_scrolls_size() == {'x': 21, 'y': 21}


def test_get_scrolls_size_firefox(driver_wrapper):
    # Update conf and create a new VisualTest instance
    driver_wrapper.config.set('Driver', 'type', 'firefox')
    visual = VisualTest(driver_wrapper)

    # Check scrolls
    assert visual.get_scrolls_size() == {'x': 0, 'y': 0}


def test_remove_scrolls(driver_wrapper):
    # Create a new VisualTest instance
    visual = VisualTest(driver_wrapper)
    visual.get_scrolls_size = lambda: {'x': 0, 'y': 17}

    # Remove scroll
    img = Image.open(file_scroll)
    img = visual.remove_scrolls(img)

    # Assert output image
    assert_image(visual, img, current_method_name(), 'register_chrome_scroll_removed')


def test_remove_scrolls_without_scroll(driver_wrapper):
    # Create a new VisualTest instance
    visual = VisualTest(driver_wrapper)
    visual.get_scrolls_size = lambda: {'x': 0, 'y': 0}

    # Remove scroll
    img = Image.open(file_scroll)
    img = visual.remove_scrolls(img)

    # Assert output image
    assert_image(visual, img, current_method_name(), 'register_chrome_scroll')


def test_mobile_resize(driver_wrapper):
    # Update conf and create a new VisualTest instance
    driver_wrapper.config.set('Driver', 'type', 'ios')
    driver_wrapper.utils.get_window_size.return_value = {'width': 375, 'height': 667}
    visual = VisualTest(driver_wrapper)

    # Resize image
    img = Image.open(file_ios)
    img = visual.mobile_resize(img)

    # Assert output image
    assert_image(visual, img, current_method_name(), 'ios_resized',
                 expected_result='equal-Distance is 0.00060770, less than 0.001 threshold', threshold=0.001)


def test_mobile_no_resize(driver_wrapper):
    # Update conf and create a new VisualTest instance
    driver_wrapper.config.set('Driver', 'type', 'ios')
    driver_wrapper.utils.get_window_size.return_value = {'width': 750, 'height': 1334}
    visual = VisualTest(driver_wrapper)

    # Resize image
    orig_img = Image.open(file_ios)
    img = visual.mobile_resize(orig_img)

    # Assert that image object has not been modified
    assert orig_img == img


def test_desktop_resize(driver_wrapper):
    # Update conf and create a new VisualTest instance
    driver_wrapper.is_mac_test = mock.MagicMock(return_value=True)
    driver_wrapper.utils.get_window_size.return_value = {'width': 1280, 'height': 1024}
    visual = VisualTest(driver_wrapper)

    # Resize image
    img = Image.open(file_mac)
    img = visual.desktop_resize(img)

    # Assert output image
    assert_image(visual, img, current_method_name(), 'mac_os_retina_resized')


def test_desktop_no_resize(driver_wrapper):
    # Update conf and create a new VisualTest instance
    driver_wrapper.is_mac_test = mock.MagicMock(return_value=True)
    driver_wrapper.utils.get_window_size.return_value = {'width': 3840, 'height': 2102}
    visual = VisualTest(driver_wrapper)

    # Resize image
    orig_img = Image.open(file_ios)
    img = visual.mobile_resize(orig_img)

    # Assert that image object has not been modified
    assert orig_img == img


def test_exclude_elements(driver_wrapper):
    # Create elements mock
    driver_wrapper.driver.execute_script.return_value = 0  # scrollX=0 and scrollY=0
    visual = VisualTest(driver_wrapper)
    web_elements = [get_mock_element(x=250, y=40, height=40, width=300),
                    get_mock_element(x=250, y=90, height=20, width=100)]
    img = Image.open(file_v1)  # Exclude elements
    img = visual.exclude_elements(img, web_elements)

    # Assert output image
    assert_image(visual, img, current_method_name(), 'register_exclude')


def test_exclude_element_outofimage(driver_wrapper):
    # Create elements mock
    visual = VisualTest(driver_wrapper)
    driver_wrapper.driver.execute_script.return_value = 0  # scrollX=0 and scrollY=0
    web_elements = [get_mock_element(x=250, y=40, height=40, width=1500)]
    img = Image.open(file_v1)

    # Exclude elements
    img = visual.exclude_elements(img, web_elements)

    # Assert output image
    assert_image(visual, img, current_method_name(), 'register_exclude_outofimage')


def test_exclude_no_elements(driver_wrapper):
    # Exclude no elements
    visual = VisualTest(driver_wrapper)
    img = Image.open(file_v1)
    img = visual.exclude_elements(img, [])

    # Assert output image
    assert_image(visual, img, current_method_name(), 'register')


def test_assert_screenshot_no_enabled_force(driver_wrapper):
    # Configure driver mock
    with open(file_v1, "rb") as f:
        image_data = f.read()
    driver_wrapper.driver.get_screenshot_as_png.return_value = image_data

    # Update conf and create a new VisualTest instance
    driver_wrapper.config.set('VisualTests', 'enabled', 'false')
    visual = VisualTest(driver_wrapper, force=True)

    # Assert screenshot
    filename = os.path.splitext(os.path.basename(file_v1))[0]
    visual.assert_screenshot(None, filename=filename, file_suffix=current_method_name())
    driver_wrapper.driver.get_screenshot_as_png.assert_called_once_with()


def test_assert_screenshot_no_enabled_force_fail(driver_wrapper):
    # Configure driver mock
    with open(file_v2, "rb") as f:
        image_data = f.read()
    driver_wrapper.driver.get_screenshot_as_png.return_value = image_data

    # Update conf and create a new VisualTest instance
    driver_wrapper.config.set('VisualTests', 'fail', 'false')
    driver_wrapper.config.set('VisualTests', 'enabled', 'false')
    visual = VisualTest(driver_wrapper, force=True)

    # Assert screenshot
    filename = os.path.splitext(os.path.basename(file_v1))[0]
    with pytest.raises(AssertionError) as exc:
        visual.assert_screenshot(None, filename=filename, file_suffix=current_method_name())
    driver_wrapper.driver.get_screenshot_as_png.assert_called_once_with()
    assert str(exc.value).endswith(f"did not match the baseline '{file_v1}' (by a distance of 0.00520373,"
                                   f" more than 0 threshold)")


def test_assert_screenshot_full_and_save_baseline(driver_wrapper):
    # Configure driver mock
    with open(file_v1, "rb") as f:
        image_data = f.read()
    driver_wrapper.driver.get_screenshot_as_png.return_value = image_data
    driver_wrapper.config.set('VisualTests', 'save', 'true')
    visual = VisualTest(driver_wrapper)

    # Assert screenshot
    filename = current_method_name()
    visual.assert_screenshot(None, filename=filename, file_suffix=current_method_name())
    output_path = os.path.join(visual.output_directory, f'01_{filename}__{current_method_name()}.png')
    driver_wrapper.driver.get_screenshot_as_png.assert_called_once_with()

    # Output image and new baseline image must be equal
    baseline_path = os.path.join(baselines_path, f'{filename}.png')
    compare_image_files(visual, current_method_name(), output_path, baseline_path)


def test_assert_screenshot_element_and_save_baseline(driver_wrapper):
    # Create element mock
    driver_wrapper.driver.execute_script.return_value = 0  # scrollX=0 and scrollY=0
    web_element = get_mock_element(x=250, y=40, height=40, width=300)

    # Configure driver mock
    with open(file_v1, "rb") as f:
        image_data = f.read()
    driver_wrapper.driver.get_screenshot_as_png.return_value = image_data
    driver_wrapper.config.set('VisualTests', 'save', 'true')
    visual = VisualTest(driver_wrapper)

    # Assert screenshot
    filename = os.path.splitext(os.path.basename(file_cropped))[0]
    visual.assert_screenshot(web_element, filename=filename, file_suffix=current_method_name())
    driver_wrapper.driver.get_screenshot_as_png.assert_called_once_with()

    # Check cropped image
    output_path = os.path.join(visual.output_directory, f'01_{filename}__{current_method_name()}.png')
    compare_image_files(visual, current_method_name(), output_path, orig_file_cropped)

    # Output image and new baseline image must be equal
    output_path_2 = os.path.join(visual.output_directory, f'02_{filename}__{current_method_name()}.png')
    shutil.copyfile(output_path, output_path_2)
    compare_image_files(visual, current_method_name(), output_path_2, file_cropped)


def test_assert_screenshot_full_and_compare(driver_wrapper):
    # Configure driver mock
    with open(file_v1, "rb") as f:
        image_data = f.read()
    driver_wrapper.driver.get_screenshot_as_png.return_value = image_data
    visual = VisualTest(driver_wrapper)

    # Assert screenshot
    filename = os.path.splitext(os.path.basename(file_v1))[0]
    visual.assert_screenshot(None, filename=filename, file_suffix=current_method_name())
    driver_wrapper.driver.get_screenshot_as_png.assert_called_once_with()


def test_assert_screenshot_element_and_compare(driver_wrapper):
    # Add baseline image
    driver_wrapper.driver.execute_script.return_value = 0  # scrollX=0 and scrollY=0
    visual = VisualTest(driver_wrapper)

    # Create element mock
    web_element = get_mock_element(x=250, y=40, height=40, width=300)

    # Configure driver mock
    with open(file_v1, "rb") as f:
        image_data = f.read()
    driver_wrapper.driver.get_screenshot_as_png.return_value = image_data

    # Assert screenshot
    filename = os.path.splitext(os.path.basename(file_cropped))[0]
    visual.assert_screenshot(web_element, filename=filename, file_suffix=current_method_name())
    driver_wrapper.driver.get_screenshot_as_png.assert_called_once_with()


def test_assert_screenshot_full_without_baseline(driver_wrapper):
    # Configure driver mock
    with open(file_v1, "rb") as f:
        image_data = f.read()
    driver_wrapper.driver.get_screenshot_as_png.return_value = image_data
    driver_wrapper.config.set('VisualTests', 'fail', 'true')
    visual = VisualTest(driver_wrapper)

    # Assert screenshot
    with pytest.raises(AssertionError) as exc:
        visual.assert_screenshot(None, filename='screenshot_does_not_exist', file_suffix=current_method_name())
    driver_wrapper.driver.get_screenshot_as_png.assert_called_once_with()
    baseline_path = os.path.join(baselines_path, 'screenshot_does_not_exist.png')
    assert str(exc.value) == f'Baseline file not found: {baseline_path}'


def test_assert_screenshot_element_without_baseline(driver_wrapper):
    # Add baseline image
    driver_wrapper.driver.execute_script.return_value = 0  # scrollX=0 and scrollY=0
    driver_wrapper.config.set('VisualTests', 'fail', 'true')
    visual = VisualTest(driver_wrapper)

    # Create element mock
    web_element = get_mock_element(x=250, y=40, height=40, width=300)

    # Configure driver mock
    with open(file_v1, "rb") as f:
        image_data = f.read()
    driver_wrapper.driver.get_screenshot_as_png.return_value = image_data

    # Assert screenshot
    with pytest.raises(AssertionError) as exc:
        visual.assert_screenshot(web_element, filename='screenshot_does_not_exist', file_suffix=current_method_name())
    driver_wrapper.driver.get_screenshot_as_png.assert_called_once_with()
    baseline_path = os.path.join(baselines_path, 'screenshot_does_not_exist.png')
    assert str(exc.value) == f'Baseline file not found: {baseline_path}'


def test_assert_screenshot_mobile_resize_and_exclude(driver_wrapper):
    # Create elements mock
    driver_wrapper.driver.execute_script.return_value = 0  # scrollX=0 and scrollY=0
    exclude_elements = [get_mock_element(x=0, y=0, height=24, width=375)]

    # Configure driver mock
    with open(file_ios, "rb") as f:
        image_data = f.read()
    driver_wrapper.utils.get_window_size.return_value = {'width': 375, 'height': 667}
    driver_wrapper.driver.get_screenshot_as_png.return_value = image_data

    # Update conf and create a new VisualTest instance
    driver_wrapper.config.set('Driver', 'type', 'ios')
    driver_wrapper.config.set('VisualTests', 'save', 'true')
    visual = VisualTest(driver_wrapper)

    # Assert screenshot
    visual.assert_screenshot(None, filename='screenshot_ios', file_suffix=current_method_name(),
                             exclude_elements=exclude_elements)
    driver_wrapper.driver.get_screenshot_as_png.assert_called_once_with()

    # Check cropped image
    expected_image = os.path.join(root_path, 'resources', 'ios_excluded.png')
    output_path = os.path.join(visual.output_directory, f'01_screenshot_ios__{current_method_name()}.png')
    compare_image_files(visual, current_method_name(), output_path, expected_image,
                        expected_result='equal-Distance is 0.00062769, less than 0.001 threshold', threshold=0.001)

    # Output image and new baseline image must be equal
    baseline_path = os.path.join(baselines_path, 'screenshot_ios.png')
    output_path_2 = os.path.join(visual.output_directory, f'02_screenshot_ios__{current_method_name()}.png')
    shutil.copyfile(output_path, output_path_2)
    compare_image_files(visual, current_method_name(), output_path_2, baseline_path)


def test_assert_screenshot_mobile_web_resize_and_exclude(driver_wrapper):
    # Create elements mock
    driver_wrapper.driver.execute_script.return_value = 0  # scrollX=0 and scrollY=0
    form_element = get_mock_element(x=0, y=0, height=559, width=375)
    exclude_elements = [get_mock_element(x=15, y=296.515625, height=32, width=345)]

    # Configure driver mock
    with open(file_ios_web, "rb") as f:
        image_data = f.read()
    driver_wrapper.utils.get_window_size.return_value = {'width': 375, 'height': 667}
    driver_wrapper.driver.get_screenshot_as_png.return_value = image_data

    # Update conf and create a new VisualTest instance
    driver_wrapper.config.set('Driver', 'type', 'ios')
    driver_wrapper.config.set('Capabilities', 'browserName', 'safari')
    driver_wrapper.config.set('VisualTests', 'save', 'true')
    visual = VisualTest(driver_wrapper)

    # Assert screenshot
    visual.assert_screenshot(form_element, filename='screenshot_ios_web', file_suffix=current_method_name(),
                             exclude_elements=exclude_elements)
    driver_wrapper.driver.get_screenshot_as_png.assert_called_once_with()

    # Check cropped image
    expected_image = os.path.join(root_path, 'resources', 'ios_web_exclude.png')
    output_path = os.path.join(visual.output_directory, f'01_screenshot_ios_web__{current_method_name()}.png')
    compare_image_files(visual, current_method_name(), output_path, expected_image,
                        expected_result='equal-Distance is 0.00018128, less than 0.001 threshold', threshold=0.001)

    # Output image and new baseline image must be equal
    baseline_path = os.path.join(baselines_path, 'screenshot_ios_web.png')
    output_path_2 = os.path.join(visual.output_directory, f'02_screenshot_ios_web__{current_method_name()}.png')
    shutil.copyfile(output_path, output_path_2)
    compare_image_files(visual, current_method_name(), output_path_2, baseline_path)


def test_assert_screenshot_str_threshold(driver_wrapper):
    visual = VisualTest(driver_wrapper)
    with pytest.raises(TypeError) as exc:
        visual.assert_screenshot(None, 'screenshot_full', threshold='name')
    assert str(exc.value) == 'Threshold must be a number between 0 and 1: name'


def test_assert_screenshot_greater_threshold(driver_wrapper):
    visual = VisualTest(driver_wrapper)
    with pytest.raises(TypeError) as exc:
        visual.assert_screenshot(None, 'screenshot_full', threshold=2)
    assert str(exc.value) == 'Threshold must be a number between 0 and 1: 2'
