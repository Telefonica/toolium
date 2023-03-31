.. _multiple_drivers:

Multiple Simultaneous Drivers
=============================

By default, Toolium creates a driver using the configuration in properties.cfg and all page objects and elements use
this driver to execute their commands. The driver is accessible from tests in self.driver.

Although it is also possible to create additional drivers with *DriverWrapper* class.

For instance, to create a driver with the same configuration as the default driver (in this case two Firefox drivers)::

    [Driver]
    type: firefox

.. code-block:: python

    second_wrapper = DriverWrapper()
    second_wrapper.connect()

To create a driver with a different configuration (in this case one Android driver and one Firefox driver)::

    [Driver]
    type: android

.. code-block:: python

    second_wrapper = DriverWrapper()
    second_wrapper.config.set('Driver', 'type', 'firefox')
    second_wrapper.connect()

The driver wrapper contains the driver instance, that can be used as a regular driver, e.g.:

.. code-block:: python

    second_wrapper.driver.find_element(BY.XPATH, '//form')

To use the second driver in page objects and their elements, pass the driver wrapper to the page object constructor:

.. code-block:: python

    login_page = LoginPageObject(second_wrapper)

and, instead of define page elements as page object attributes, create them inside *init_page_elements* method:

.. code-block:: python

    class LoginPageObject(PageObject):
        def init_page_elements(self):
            self.username = InputText(By.ID, 'username')
            self.password = InputText(By.ID, 'password')
