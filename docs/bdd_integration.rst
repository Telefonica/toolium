.. _bdd_integration:

BDD Integration
===============

Toolium can be also used with behave and lettuce tests.

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
- :code:`context.driver`: Selenium or Appium driver instance
- :code:`context.utils`: :ref:`Utils <utils>` instance

Behave userdata properties
--------------------------

Toolium properties can be modified from behave userdata configuration. For example, to select the driver type from
command line instead of using the driver type defined in properties.cfg:

.. code:: console

    $ behave -D Driver_type=chrome

Behave tags
-----------

Toolium defines two tags to configure driver:

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


Lettuce
~~~~~~~

Lettuce tests should be developed as usual, only *terrain.py* file should be modified to initialize driver and the rest
of Toolium configuration.

Terrain methods should call to the corresponding Toolium terrain methods, as can be seen in the following example:

.. code-block:: python

    from lettuce import after, before
    from toolium.lettuce.terrain import (setup_driver as toolium_setup_driver, teardown_driver as toolium_teardown_driver,
                                         teardown_driver_all as toolium_teardown_driver_all)


    @before.each_scenario
    def setup_driver(scenario):
        toolium_setup_driver(scenario)


    @after.each_scenario
    def teardown_driver(scenario):
        toolium_teardown_driver(scenario)


    @after.all
    def teardown_driver_all(total):
        toolium_teardown_driver_all(total)


After initialization, the following attributes will be available in world object:

- :code:`world.toolium_config`: dictionary with Toolium configuration, readed from properties.cfg
- :code:`world.driver_wrapper`: :ref:`DriverWrapper <driver_wrapper>` instance
- :code:`world.driver`: Selenium or Appium driver instance
- :code:`world.utils`: :ref:`Utils <utils>` instance
