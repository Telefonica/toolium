.. _page_objects:

Page Objects
============

Toolium implements Page Object pattern, where a page object represents a web page or a mobile screen (or a part of them)
and a page element is any of the elements contained in those pages (inputs, buttons, texts, ...).

Toolium loads page elements in lazy loading, so they are searched in Selenium or Appium when they are used, not when
they are defined.

Basic usage
-----------

To define a page object in Toolium, first create a class derived from *PageObject* and add a class attribute for each
page element. Take into account that each page element has two mandatory initialization arguments: locator type and
locator value. Besides, page object class must implement a method for each action allowed in this page.

Example of a page object definition:

.. code-block:: python

    from toolium.pageobjects.page_object import PageObject
    from toolium.pageelements import InputText, Button

    class LoginPageObject(PageObject):
        username = InputText(By.ID, 'username')
        password = InputText(By.ID, 'password')
        login_button = Button(By.XPATH, "//form[@id='login']/button")

        def login(self, username, password):
            self.username.text = username
            self.password.text = password
            self.login_button.click()

Example of a test using the previous page object:

.. code-block:: python

    def test_login(self):
        LoginPageObject().login('user', 'pass')
        ...

Page element types
------------------

There are different page elements classes that represent different element types of a page:
:ref:`Text <text_page_element>`, :ref:`Button <button_page_element>`, :ref:`InputText <input_text_page_element>`,
:ref:`Checkbox <checkbox_page_element>`, :ref:`InputRadio <input_radio_page_element>`, :ref:`Link <link_page_element>`,
:ref:`Select <select_page_element>` and :ref:`Group <group_page_element>`.

For any other existing element type, :ref:`PageElement <page_element>` class can be used.

Methods
~~~~~~~

Each element type has specific methods to get text, set text (InputText), select an option (Select) or click the
element (Button), for example.

.. code-block:: python

    username = InputText(By.ID, 'username')

    # Get text value
    input_value = username.text

    # Set text value
    username.text = 'username'

Page elements only implement the most commonly used methods. When performing any other action with the element, get the
web element of the page element and execute the action. *web_element* property returns the Selenium or Appium
WebElement.

.. code-block:: python

    username = InputText(By.ID, 'username')

    # Check if the element is enabled
    enabled = username.web_element.is_enabled()

Parent
~~~~~~

Page elements have an optional argument *parent*, that points to the container of the element. The page element will be
searched within the parent element, instead of the entire page. The parent can be a PageElement, a WebElement or a
locator tuple.

.. code-block:: python

    form = PageElement(By.XPATH, "//form[@id='login']")
    login_button = Button(By.XPATH, "./button", parent=form)


Group
~~~~~

Group is a page element that contains other child page elements, that will be searched within the group element,
instead of the entire page.

.. code-block:: python

    from toolium.pageobjects.page_object import PageObject
    from toolium.pageelements import InputText, Button, Group

    class Form(Group):
        username = InputText(By.ID, 'username')
        password = InputText(By.ID, 'password')
        login_button = Button(By.XPATH, "./button")

    class LoginPageObject(PageObject):
        form = Form(By.XPATH, "//form[@id='login']")

        def login(self, username, password):
            self.form.username.text = username
            self.form.password.text = password
            self.form.login_button.click()


Find multiple page elements
---------------------------

Toolium provides some new classes that represent lists of page elements: :ref:`PageElements <page_elements>`,
:ref:`Texts <page_elements>`, :ref:`Buttons <page_elements>`, :ref:`InputTexts <page_elements>`,
:ref:`Checkboxes <page_elements>`, :ref:`InputRadios <page_elements>`, :ref:`Links <page_elements>`,
:ref:`Selects <page_elements>` and :ref:`Groups <page_elements>`.

These lists help execute an action on all their elements, for example to clear all inputs of a web page:

.. code-block:: python

    inputs = InputTexts(By.XPATH, '//input')

    for input in inputs.page_elements:
        input.clear()

Concurrency issues
------------------

If using multiple instances of a page object class at the same time (e.g. having two simultaneous drivers), class
attributes can not be used to define page elements. In this case, page elements must be defined as instance attributes
through a method called *init_page_elements*.

.. code-block:: python

    from toolium.pageobjects.page_object import PageObject
    from toolium.pageelements import InputText, Button

    class LoginPageObject(PageObject):
        def init_page_elements(self):
            self.username = InputText(By.ID, 'username')
            self.password = InputText(By.ID, 'password')
            self.login_button = Button(By.XPATH, "//form[@id='login']/button")

        def login(self, username, password):
            self.username.text = username
            self.password.text = password
            self.login_button.click()
