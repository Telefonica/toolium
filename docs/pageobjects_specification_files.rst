.. _pageobjects_specification_files:

PageObject Definition Files
===========================

PageObjects Specification Files use a Specific Domain Language implemented by Toolium that allows to define PageObjects
following a human-readable specification in YAML. This specification is built and, as result of this, PageObject with
all the expected PageElements and its configuration are loaded by Toolium, to use it as part of all test cases or
whatever implementation using this framework.

This way of test developing makes possible to "model" web pages and mobile views easily avoiding the implementation
of custom Python classes.

Toolium configuration
---------------------

To enable and configure this feature, it is needed to properly set the following configuration as part of the
:code:`conf/properties.cfg`::


    [PageObjectSpecFiles]
    enabled: true
    spec_files_path: resources/pageobject_spec_files
    custom_page_object_module_path: common/pageobjects
    custom_page_elements_module_path: common/pageelements

* :code:`enabled`: To enable the loading of PageObjects from Specification Files.
* :code:`spec_files_path`: Path where PageObject Specification Files are located.
* :code:`custom_page_object_module_path`: Path (directory) where custom PageObjects are implemented in your project
* :code:`custom_page_elements_module_path`: Path (directory) where custom PageElements are implemented in your project


PageObject and PageElements implementation
------------------------------------------

The implementation of PageObjects allow to define all PageElements implemented by default as part of Toolium.

.. code-block:: yaml

    Login :
      - Text        :
          Name            : form
          Locator-Type    : ID
          Locator-Value   : d0f81d3c-d8b0-476b-bcd5-d22ab0153cad
          Wait-For-Loaded : True
      - InputText   :
          Name            : username
          Locator-Type    : ID
          Locator-Value   : username
          Wait-For-Loaded : True
      - InputText   :
          Name            : password
          Locator-Type    : ID
          Locator-Value   : password
          Wait-For-Loaded : True
      - Text :
          Name            : error
          Locator-Type    : ID
          Locator-Value   : 6aba7bba-5bdb-4fc9-9c3d-b64719b6d80e
          Wait-For-Loaded : False

The example above is a model of a Web Page (or mobile view) with the following data:

- The name of the page object is: "Login". Toolium will identify this page object by this name.
- The PageObject will have four page elements.
- When waiting for this PageObject loaded, the framework will wait for all its page elements with property
```Wait-For-Loaded : True```

Each PageElement has the following data:

- The type of PageElement (Text, InputText, etc).
- The name of the PageElement. This name will be the one used to instantiate the page element into the page object.
- The locator type. Accepted values are the ones accepted by Selenium or Appium (XPATH, ID, CLASS_NAME, etc).
- The value for that locator in order to "locate" the element into the view.
- A flag to specify that the page can be considered completely loaded when this page element is visible.
