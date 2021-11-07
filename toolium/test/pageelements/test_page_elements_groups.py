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

import mock
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.pageelements import PageElements, Group, InputText, Link
from toolium.pageobjects.page_object import PageObject


class Column(Group):
    def init_page_elements(self):
        self.input = InputText(By.XPATH, './/input')
        self.link = Link(By.XPATH, './/a')
        self.input_with_parent = InputText(By.XPATH, './/input', parent=self.link)


class Columns(PageElements):
    page_element_class = Column


class Row(Group):
    def init_page_elements(self):
        self.columns = Columns(By.XPATH, './/td')


class Rows(PageElements):
    page_element_class = Row


class TablePageObject(PageObject):
    def init_page_elements(self):
        self.rows = Rows(By.XPATH, '//table//tr')


@pytest.fixture
def driver_wrapper():
    # Reset wrappers pool values
    DriverWrappersPool._empty_pool()
    DriverWrapper.config_properties_filenames = None

    # Create a new wrapper
    driver_wrapper = DriverWrappersPool.get_default_wrapper()
    driver_wrapper.driver = mock.MagicMock()

    return driver_wrapper


def test_reset_object_page_elements_groups(driver_wrapper):
    # Mock Driver.save_web_element = True
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.getboolean_optional.return_value = True
    # Create mock rows
    mock_element_1 = mock.MagicMock(spec=WebElement)
    mock_element_2 = mock.MagicMock(spec=WebElement)
    driver_wrapper.driver.find_elements.side_effect = [[mock_element_1, mock_element_2]]
    # Create mock columns
    mock_element_11 = mock.MagicMock(spec=WebElement)
    mock_element_12 = mock.MagicMock(spec=WebElement)
    mock_element_1.find_elements.return_value = [mock_element_11]
    mock_element_2.find_elements.return_value = [mock_element_12]

    table_page = TablePageObject()

    # Get elements for each row and column
    for row in table_page.rows.page_elements:
        for column in row.columns.page_elements:
            column.input.web_element
            column.link.web_element
            column.input_with_parent.web_element

    # Check that web and page elements are filled in rows
    assert len(table_page.rows._web_elements) == 2
    row_1 = table_page.rows._page_elements[0]
    row_2 = table_page.rows._page_elements[1]
    assert row_1._web_element is not None
    assert row_2._web_element is not None
    # Check that web and page elements are filled in columns
    assert len(row_1.columns._web_elements) == 1
    assert len(row_1.columns._web_elements) == 1
    column_11 = row_1.columns._page_elements[0]
    column_21 = row_2.columns._page_elements[0]
    assert column_11._web_element is not None
    assert column_21._web_element is not None
    # Check that web elements are filled
    assert column_11.input._web_element is not None
    assert column_11.link._web_element is not None
    assert column_11.input_with_parent._web_element is not None
    assert column_21.input._web_element is not None
    assert column_21.link._web_element is not None
    assert column_21.input_with_parent._web_element is not None
    # Check that the group elements have the group as parent, except input_with_parent that has its custom parent
    assert column_11.parent == row_1
    assert column_21.parent == row_2
    assert column_11.input.parent == column_11
    assert column_11.link.parent == column_11
    assert column_11.input_with_parent.parent == column_11.link
    assert column_21.input.parent == column_21
    assert column_21.link.parent == column_21
    assert column_21.input_with_parent.parent == column_21.link

    table_page.reset_object()

    # Check that web and page elements are reset in rows
    assert len(table_page.rows._web_elements) == 0
    assert len(table_page.rows._page_elements) == 0
    assert row_1._web_element is None
    assert row_2._web_element is None
    # Check that web and page elements are reset in columns
    assert len(row_1.columns._web_elements) == 0
    assert len(row_1.columns._web_elements) == 0
    assert column_11._web_element is None
    assert column_21._web_element is None
    # Check that web element are reset
    assert column_11.input._web_element is None
    assert column_11.link._web_element is None
    assert column_11.input_with_parent._web_element is None
    assert column_21.input._web_element is None
    assert column_21.link._web_element is None
    assert column_21.input_with_parent._web_element is None
    # Check that the group elements have the group as parent, except input_with_parent that has its custom parent
    assert column_11.parent == row_1
    assert column_21.parent == row_2
    assert column_11.input.parent == column_11
    assert column_11.link.parent == column_11
    assert column_11.input_with_parent.parent == column_11.link
    assert column_21.input.parent == column_21
    assert column_21.link.parent == column_21
    assert column_21.input_with_parent.parent == column_21.link
