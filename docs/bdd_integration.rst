.. _bdd_integration:

BDD Integration
===============

Toolium can be also used with behave and lettuce tests.

Behave
------

Behave tests should be developed as usual, only *environment.py* file should be modified to initialize driver and the
rest of Toolium configuration.

Environment methods should call to the corresponding Toolium environment methods, as can be seen in the following
example:

.. code-block:: python

    from toolium.behave.environment import (before_all as toolium_before_all, before_scenario as toolium_before_scenario,
                                            after_scenario as toolium_after_scenario, after_all as toolium_after_all)


    def before_all(context):
        toolium_before_all(context)


    def before_scenario(context, scenario):
        toolium_before_scenario(context, scenario)


    def after_scenario(context, scenario):
        toolium_after_scenario(context, scenario)


    def after_all(context):
        toolium_after_all(context)


After initialization, the following attributes will be available in behave context:

- context.toolium_config: dictionary with Toolium configuration, readed from properties.cfg
- context.driver_wrapper: :ref:`DriverWrapper <driver_wrapper>` instance
- context.driver: Selenium or Appium driver instance
- context.utils: :ref:`Utils <utils>` instance

Toolium properties can be modified from behave userdata configuration. For example, to select the driver type from
command line instead of using the driver type defined in properties.cfg:

.. code:: console

    $ behave -D Driver_type=chrome

Lettuce
-------

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

- world.toolium_config: dictionary with Toolium configuration, readed from properties.cfg
- world.driver_wrapper: :ref:`DriverWrapper <driver_wrapper>` instance
- world.driver: Selenium or Appium driver instance
- world.utils: :ref:`Utils <utils>` instance
