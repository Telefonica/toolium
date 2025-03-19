.. _bdd_integration:

BDD Integration
===============

Behave
~~~~~~

Behave tests should be developed as usual, only *environment.py* file should be modified to initialize driver and the
rest of Toolium configuration.

Environment methods should call to the corresponding Toolium environment methods, as can be seen in the following
example:

.. code-block:: python

    from toolium.behave.environment import (before_all as toolium_before_all, before_feature as toolium_before_feature,
                                            before_scenario as toolium_before_scenario,
                                            after_scenario as toolium_after_scenario,
                                            after_feature as toolium_after_feature, after_all as toolium_after_all)


    def before_all(context):
        toolium_before_all(context)


    def before_feature(context, feature):
        toolium_before_feature(context, feature)


    def before_scenario(context, scenario):
        toolium_before_scenario(context, scenario)


    def after_scenario(context, scenario):
        toolium_after_scenario(context, scenario)


    def after_feature(context, feature):
        toolium_after_feature(context, feature)


    def after_all(context):
        toolium_after_all(context)


After initialization, the following attributes will be available in behave context:

- :code:`context.toolium_config`: dictionary with Toolium configuration, readed from properties.cfg
- :code:`context.driver_wrapper`: :ref:`DriverWrapper <driver_wrapper>` instance
- :code:`context.driver`: Selenium, Playwright or Appium driver instance
- :code:`context.utils`: :ref:`Utils <utils>` instance

Behave userdata properties
--------------------------

Toolium properties can be modified from behave userdata configuration. For example, to select the driver type from
command line instead of using the driver type defined in properties.cfg:

.. code:: console

    $ behave -D Driver_type=chrome

Behave tags
-----------

Toolium defines three tags to configure driver:

* :code:`@reuse_driver`: feature tag to indicate that all scenarios in this feature should share the driver. The browser will not be closed between tests.
* :code:`@reset_driver`: identifies a scenario that should not reuse the driver. The browser will be closed and reopen before this test.
* :code:`@no_driver`: identifies a scenario or feature that should not start the driver, typically in API tests.

And other scenario tags to configure Appium tests:

* :code:`@no_reset_app`: mobile app will not be reset before test (i.e. no-reset Appium capability is set to true)
* :code:`@reset_app`: mobile app will be reset before test (i.e. no-reset and full-reset Appium capabilities are set to false)
* :code:`@full_reset_app`: mobile app will be full reset before test (i.e. full-reset Appium capability is set to true)
* :code:`@android_only`: identifies a scenario that should only be executed in Android
* :code:`@ios_only`: identifies a scenario that should only be executed in iOS

Behave - Dynamic Environment
----------------------------

Optionally, some actions (labels) are defined in the Feature description as:

* Actions Before the Feature:
* Actions Before each scenario:
* Actions After each scenario:
* Actions After the Feature:

With a steps list executed in each moment identified with the label as the environment.py file. These steps are defined
similar to others one.

Each step block is separated by a blank line.

Behave keywords are supported  (Given, When, Then, And, But, Check, Setup).

.. note:: When using Drivers, **Actions Before the Feature** and **Actions After the Feature** directives
          (in the "dynamic environment" of a Feature) are only available if the execution for that Feature
          has been configured to **reuse the driver**. Otherwise, unexpected exceptions can be raised and
          execution may not finish successfully.

Example::

        @reuse_driver
        Feature: Tests with the dynamic environment
          As a behave operator using multiples scenarios
          I want to append actions before the feature, before each scenario, after each scenario and after the feature.

          Actions Before the Feature:
            Given wait 3 seconds
            And waitrty 3 seconds
            And wait 3 seconds
            And step with a table
              | parameter     | value       |
              | sub_fields_1  | sub_value 1 |
              | sub_fields_2  | sub_value 2 |

          Actions Before each Scenario:
            Given the user navigates to the "www.google.es" url
            When the user logs in with username and password
            And wait 1 seconds
            And wait 1 seconds

          Actions After each Scenario:
            And wait 2 seconds
            And wait 2 seconds

          Actions After the Feature:
            And wait 4 seconds
            And step with another step executed dynamically
            And wait 4 seconds


All kind of steps are allowed:

- with tables
- executing another step internally

In case that a step of dynamic environment fails, an exception is printed on console, i.e. 'waitrty 3 seconds' step.
When this happens, steps of the affected scenarios for that precondition are not executed (skipped) and, after that,
first step defined in those scenarios will be automatically failed because of that precondition exception,
in order to properly fail the execution and show the stats.

Behave variables transformation
-------------------------------

Toolium provides a set of functions that allow the transformation of specific string tags into different values.
See below their values, along with their associated replacement logic (click `here <https://toolium.readthedocs.io/en/latest/toolium.utils.html#toolium.utils.dataset.replace_param>`_  or check the :ref:`dataset <dataset>` module for more implementation details):

* :code:`[STRING_WITH_LENGTH_XX]`: Generates a fixed length string
* :code:`[INTEGER_WITH_LENGTH_XX]`: Generates a fixed length integer
* :code:`[STRING_ARRAY_WITH_LENGTH_XX]`: Generates a fixed length array of strings
* :code:`[INTEGER_ARRAY_WITH_LENGTH_XX]`: Generates a fixed length array of integers
* :code:`[JSON_WITH_LENGTH_XX]`: Generates a fixed length JSON
* :code:`[MISSING_PARAM]`: Generates a None object
* :code:`[NULL]`: Generates a None object
* :code:`[TRUE]`: Generates a boolean True
* :code:`[FALSE]`: Generates a boolean False
* :code:`[EMPTY]`: Generates an empty string
* :code:`[B]`: Generates a blank space
* :code:`[UUID]`: Generates a v4 UUID
* :code:`[RANDOM]`: Generates a random value
* :code:`[RANDOM_PHONE_NUMBER]`: Generates a random phone number for language and country configured in dataset.language and dataset.country
* :code:`[TIMESTAMP]`: Generates a timestamp from the current time
* :code:`[DATETIME]`: Generates a datetime from the current time (UTC)
* :code:`[NOW]`: Similar to DATETIME without microseconds; the format depends on the language
* :code:`[NOW(%Y-%m-%dT%H:%M:%SZ)]`: Same as NOW but using an specific format by the python strftime function of the datetime module. When using the %f placeholder, the number of digits to be used can be set like this: %3f
* :code:`[NOW + 2 DAYS]`: Similar to NOW but two days later
* :code:`[NOW - 1 MINUTES]`: Similar to NOW but one minute earlier
* :code:`[NOW(%Y-%m-%dT%H:%M:%SZ) - 7 DAYS]`: Similar to NOW but seven days before and with the indicated format
* :code:`[TODAY]`: Similar to NOW without time; the format depends on the language
* :code:`[TODAY + 2 DAYS]`: Similar to NOW, but two days later
* :code:`[STR:xxxx]`: Cast xxxx to a string
* :code:`[INT:xxxx]`: Cast xxxx to an int
* :code:`[FLOAT:xxxx]`: Cast xxxx to a float
* :code:`[LIST:xxxx]`: Cast xxxx to a list
* :code:`[DICT:xxxx]`: Cast xxxx to a dict
* :code:`[UPPER:xxxx]`: Converts xxxx to upper case
* :code:`[LOWER:xxxx]`: Converts xxxx to lower case
* :code:`[REPLACE:xxxx::SUBSTRING_TO_BE_REPLACED::SUBSTRING_TO_USE_AS_REPLACEMENT]`: Replaces a substring with another in xxxx string
* :code:`[TITLE:xxxx]`: Applies python's string title() method to xxxx string
* :code:`[ROUND:xxxx::N]`: Rounds given number xxxx to N digits in its fractional part


There are also some special tags that allow to use parameter values configured at different sources defined by the `map_param <https://toolium.readthedocs.io/en/latest/toolium.utils.html#toolium.utils.dataset.map_param>`_ method:

* :code:`[CONF:xxxx]`: Value from the config dict in dataset.project_config for the key xxxx
* :code:`[LANG:xxxx]`: String from the texts dict in dataset.language_terms for the key xxxx, using the language specified in dataset.language
* :code:`[POE:xxxx]`: Definition(s) from the POEditor terms list in dataset.poeditor_terms for the term xxxx (see :ref:`poeditor <poeditor>` module for details)
* :code:`[TOOLIUM:xxxx]`: Value from the toolium config in dataset.toolium_config for the key xxxx
* :code:`[CONTEXT:xxxx]`: Value from the behave context storage dict in dataset.behave_context for the key xxxx, or value of the behave context attribute xxxx, if the former does not exist
* :code:`[ENV:xxxx]`: Value of the OS environment variable xxxx
* :code:`[FILE:xxxx]`: String with the content of the file in the path xxxx
* :code:`[BASE64:xxxx]`: String with the base64 representation of the file content in the path xxxx

In order to apply string replacements at code level, the following functions are available in the context. E.g.::

.. code:: console

    from toolium.utils.dataset import map_param, replace_param

    mapped_param = map_param('[TOOLIUM:Driver_chrome_driver_path]')
    replaced_param = replace_param('[NOW - 1 MINUTES]')


Type inference
^^^^^^^^^^^^^^

By default, the param replacements do not infer primitive types. To enable the type inference
when using the `replace_param` function you have to add the following configuration:

.. code:: console

    [TestExecution]
    infer_datatypes: true


POEditor tags
^^^^^^^^^^^^^

POE tag returns a list of texts or a single text (if only one result) from POEditor for the given resource.

Language used to get texts in POEditor will be get from toolium config file ([TestExecution] language):

.. code:: console

    [TestExecution]
    language: es-es
    poeditor_mode: offline

poeditor_mode with value offline will try to get a local copy of POEditor terms from output directory, online mode (by default if not provided) will download always terms from POEditor.
If provided will override poeditor mode parameter defined in properties file.

In your ENV-properties.json file add this block:

.. code:: console

    "poeditor": {
        "base_url": "https://api.poeditor.com",
        "api_token": "XXXXX",
        "project_name": "Aura-Bot",
        "prefixes": [],
        "key_field": "reference",
        "search_type": "contains",
        "mode": "online",
        "file_path": "resources/poeditor/poeditor_terms.json"
    }

* api_token can be generated from POEditor in this url: https://poeditor.com/account/api

* api_token can also be configured from a system property called `poeditor_api_token`

* prefixes contains a list of references prefixes that can be used to search the reference

For example, if prefixes = ['PRE.'], POE returns the value of 'PRE.reference' if this reference exists otherwise it
returns the value of 'reference'

* key_field can be any field of POEditor text structure. The default value is "reference"

* search_type can be "contains" if more than one result is expected or "exact" if only one result is expected. The default value is "contains"

* mode with value offline will try to get a local copy of POEditor terms from output directory, online mode (by default if not provided) will download always terms from POEditor

* file_path contains relative path of downloaded POEditor terms file (default value: _output/poeditor_terms.json)
