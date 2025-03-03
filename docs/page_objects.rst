.. _page_objects:

Page Objects
============

Toolium implements Page Object pattern, where a page object represents a web page or a mobile screen (or a part of them)
and a page element is any of the elements contained in those pages (inputs, buttons, texts, ...).

Toolium loads page elements in lazy loading, so they are searched in Selenium, Playwright or Appium when they are used,
not when they are defined.

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

.. _page_element_types:

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
web element of the page element and execute the action. *web_element* property returns the Selenium, Playwright or
Appium WebElement.

.. code-block:: python

    username = InputText(By.ID, 'username')

    # Check if the element is enabled
    enabled = username.web_element.is_enabled()

.. _page_element_parent:

Parent
~~~~~~

Page elements have an optional argument *parent*, that points to the container of the element. The page element will be
searched within the parent element, instead of the entire page. The parent can be a PageElement, a WebElement or a
locator tuple.

.. code-block:: python

    form = PageElement(By.XPATH, "//form[@id='login']")
    login_button = Button(By.XPATH, "./button", parent=form)

Shadowroot
~~~~~~~~~~

Page elements have an optional argument *shadowroot*, with the CSS selector of the shadowroot parent. The page element
will be searched within the shadowroot parent element, instead of the entire page.

It is only supported for PageElement objects identified by CSS, so it is not supported for PageElements, Group,
elements with nested encapsulation or PageElement identified by other selector types.

.. code-block:: python

    login_button = Button(By.CSS_SELECTOR, "css_selector", shadowroot="shadowroot_css_selector")

Webview
~~~~~~~~~~

Page elements have an optional argument *webview*, a boolean that indicates if the page element is in a webview context
(default value is False). Only apply to mobile tests, where we need to do a change to webview context to find an
element, which is in a webview. This argument will be used only if the configuration property
*automatic_context_selection* is True.

If *webview* argument is True but webview_context_selection_callback is not defined, then the default webview context
change behaviour will apply. This behaviour depends on the mobile client:

- Android: The first window handle of the appPackage webview context will be selected.
- iOS: The last webview context of the APP bundleID will be selected.

If this default behaviour is not valid for our app (for example has more than one webview context), we can use the
following optional parameters to define a custom logic that is executed at runtime:

- webview_context_selection_callback: Method provided to select the desired webview context if
  automatic_context_selection is enabled. Must return a tuple (context, window_handle) for android, and a context for ios.
- webview_csc_args: arguments list for webview_context_selection_callback.

To use this functionality appium version must be greater or equal to 1.17. (where mobile:getContexts functionality was
added to iOS)

.. code-block:: python

    login_button = Button(By.XPATH, "//*[@data-qsysid='subscription-counters']/div/div/", webview=True,
                          webview_context_selection_callback = webview_context_selector_per_url,
                          webview_csc_args = [driver_wrapper, WebviewConfigHelper.get_helper().account])

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

Mobile page object
------------------

MobilePageObject class allows using the same test case in Android and iOS, because an Android or iOS page object is
instantiated depending on driver configuration. It's useful when testing the same mobile application in Android and iOS.

Three page objects must be defined: a base page object with the commons methods, derived from MobilePageObject, and an
Android and iOS page objects with their specific locators and methods, derived from base page object.

For example, a base page object for login functionality:

.. code-block:: python

    from toolium.pageobjects.mobile_page_object import MobilePageObject

    class BaseLoginPageObject(MobilePageObject):
        def login(self, username, password):
            self.username.text = username
            self.password.text = password
            self.login_button.click()

The corresponding Android page object, where page elements are defined with their specific Android locators:

.. code-block:: python

    from appium.webdriver.common.appiumby import AppiumBy
    from toolium.pageelements import InputText, Button
    from toolium_examples.pageobjects.base.login import BaseLoginPageObject

    class AndroidLoginPageObject(BaseLoginPageObject):
        username = InputText(AppiumBy.ID, 'io.appium.android.apis:id/username')
        password = InputText(AppiumBy.ID, 'io.appium.android.apis:id/password')
        login_button = Button(AppiumBy.ID, "io.appium.android.apis:id/login_button")


And the iOS page object, where page elements are defined with their specific iOS locators:

.. code-block:: python

    from appium.webdriver.common.appiumby import AppiumBy
    from toolium.pageelements import InputText, Button
    from toolium_examples.pageobjects.base.login import BaseLoginPageObject

    class IosLoginPageObject(BaseLoginPageObject):
        username = InputText(AppiumBy.IOS_UIAUTOMATION, '.textFields()[0]')
        password = InputText(AppiumBy.IOS_UIAUTOMATION, '.secureTextFields()[0]')
        login_button = Button(AppiumBy.IOS_UIAUTOMATION, '.buttons()[0]')


Base, Android and iOS page objects must be defined in different files following this structure::

    FOLDER/base/MODULE_NAME.py
        class BasePAGE_OBJECT_NAME(MobilePageObject)

    FOLDER/android/MODULE_NAME.py
        class AndroidPAGE_OBJECT_NAME(BasePAGE_OBJECT_NAME)

    FOLDER/ios/MODULE_NAME.py
        class IosPAGE_OBJECT_NAME(BasePAGE_OBJECT_NAME)

This structure for the previous login example should look like::

    toolium_examples/pageobjects/base/login.py
        class BaseLoginPageObject(MobilePageObject)

    toolium_examples/pageobjects/android/login.py
        class AndroidLoginPageObject(BaseLoginPageObject)

    toolium_examples/pageobjects/ios/login.py
        class IosLoginPageObject(BaseLoginPageObject)

If page objects are simple enough, the three page objects could be defined in the same file, so the previous folder
structure is not needed.

Finally, test cases must use base page object instead of Android or iOS. During test execution, depending on the driver
type value, the corresponding Android or iOS page object will be instantiated.

.. code-block:: python

    from toolium_examples.pageobjects.base.login import BaseLoginPageObject

    class Login(AppiumTestCase):
        def test_login(self):
            BaseLoginPageObject().login(username, password)
