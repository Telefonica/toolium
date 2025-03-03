.. _playwright_configuration:

Playwright Configuration
========================

Playwright is an alternative to Selenium to test web applications using toolium. This integration is currently in beta
version.

To choose Playwright instead of Selenium, configure :code:`web_library` property in :code:`[Driver]` section in
:code:`conf/properties.cfg` file with :code:`playwright` and configure the browser in :code:`type` property as in
Selenium tests.

The following example shows how to configure toolium to run tests on Chrome using Playwright::

    [Driver]
    web_library: playwright
    type: chrome

Features not supported yet
--------------------------

The following toolium features are not supported yet when using Playwright:

* :ref:`Page Elements <page_element_types>`: not all page elements are implemented for Playwright. Currently only
  :ref:`Text <playwright_text_page_element>` and :ref:`Button <playwright_button_page_element>` page elements are
  implemented.
* :ref:`Element Parent <page_element_parent>`: elements can not be located inside another element using Playwright.
* Locators: only :code:`id` and :code:`xpath` locators are implemented for Playwright.
