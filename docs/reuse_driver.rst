.. _reuse_driver:

Reuse driver
============

By default, in Toolium, the driver is initialized and closed before and after each test. This isolates tests avoiding
problems by sharing resources, but also means that tests are slower. Reusing the driver will speed up your tests execution,
but it needs a careful handling of the initial status of each test.

There are several properties that show how to reuse the driver. They are under :code:`[Driver]` section
in :code:`conf/properties.cfg`::

    [Driver]
    reuse_driver: true
    reuse_driver_session: false
    restart_driver_after_failure: true

* :code:`reuse_driver`: if enabled, driver will be reused within the scope of a class in unittest, a module in pytest and a feature in behave.
* :code:`reuse_driver_session`: if enabled, driver will be reused for all the tests in the execution. When using behave or pytest, the driver will be closed after all tests, but if you are using unittest, the driver will remain open after tests.
* :code:`restart_driver_after_failure`: if enabled, driver will always be restarted after a failure in a test.


Behave tags
-----------

Independently of the properties configuration, Toolium defines two behave tags to configure driver:

* :code:`@reuse_driver`: feature tag to indicate that all scenarios in this feature should share the driver. The browser will not be closed between tests.
* :code:`@reset_driver`: identifies a scenario that should not reuse the driver. The browser will be closed and reopen before this test.
