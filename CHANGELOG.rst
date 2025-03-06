Toolium Changelog
=================

v3.4.1
------

*Release date: In development*

v3.4.0
------

*Release date: 2025-03-06*

- Now Playwright is available to run web tests instead of Selenium by configuring `web_library: playwright` in [Driver]
  section
- Allow setting the number of decimal places for seconds when using the `[NOW]` replacement with a specific format

v3.3.1
------

*Release date: 2025-02-05*

- Allow to save the diff image in jpg format for visual tests working with jpg
- Fix the use of the # character in the actions defined in the feature description (Actions Before/After...)

v3.3.0
------

*Release date: 2024-11-26*

- Allow negative indexes for list elements in context searches. Example: [CONTEXT:element.-1]
- Add support for JSON strings to the `DICT` and `LIST`` replacement. Example: [DICT:{"key": true}], [LIST:[null]]
- Add `REPLACE` replacement, to replace a substring with another. Example: [REPLACE:[CONTEXT:some_url]::https::http]
- Add `TITLE` replacement, to apply Python's title() function. Example: [TITLE:the title]
- Add `ROUND` replacement, float number to a string with the indicated number of decimals. Example: [ROUND:3.3333::2]
- Remove accents from generated file names to avoid errors in some filesystems
- Update Appium-Python-Client requirement to enable 3 and 4 versions
- Deprecate set_text method in InputText class to make it compatible with Appium-Python-Client 3 and 4

v3.2.0
------

*Release date: 2024-09-13*

- Add `run_storage` dictionary to context to store information during the whole test execution
- Update current ChainMap context storages (context.storage, context.feature_storage and context.run_storage)
- Allow to store values from steps into desire storage by using [key], [FEATURE:key] and [RUN:key]

v3.1.5
------

*Release date: 2024-07-15*

- Fix `export_poeditor_project` method allowing empty export response
- Add `key=value` expressions for selecting elements in the context storage
- Upgrade Faker version to 25.9.*
- Fix result for action before the feature with error and background to fail scenarios

v3.1.4
------

*Release date: 2024-03-25*

- Add `ignore_empty` optional parameter to POEditor configuration to ignore empty translations
- Ignore not found excluded elements in visual tests
- Fix duration calling to Appium `swipe` method
- Fix `[STRING_WITH_LENGTH_NN]` replacement for string with length inside a longer string

v3.1.3
------

*Release date: 2024-02-06*

- Fix `PageElements` class initialization when custom page element classes don't have all optional attributes

v3.1.2
------

*Release date: 2024-02-05*

- Upgrade Pillow version to 10.1.* to fix compatibility with Python 3.12

v3.1.1
------

*Release date: 2024-02-02*

- Add support for Python 3.12
- Upgrade Sphinx version from 4.* to 7.* to fix readthedocs theme format
- Upgrade readthedocs-sphinx-search to 0.3.2 to fix security vulnerability
- Do not log warning messages when toolium system properties are used
- Allow to initialize a `PageElements` class with webview attributes

v3.1.0
------

*Release date: 2023-09-19*

- Update `[CONTEXT:a.b.c]` replacement to allow lists access, e.g. [CONTEXT:list.1] to access the second element of list
- Add capabilities configured in `[Capabilities]` section also to Appium tests to use `platformName` and `browserName`
  w3c capabilities instead of Appium ones
- `platformVersion` Appium capability must be a string
- Add optional parameter to `compare_downloaded_files` method to allow to compare files with different names
- Remove Python 3.7 support (Python 3.7 reached the end of its life on June 27th, 2023)
- Update _android_automatic_context_selection method to be compatible with latest chromedriver versions

v3.0.2
------

*Release date: 2023-06-08*

- `context.storage` must be initialized before dynamic environment steps in `before_feature` method
- Mark scenario as failed when a dynamic environment step fails in `before_scenario`
- Mark all feature scenarios as failed when a dynamic environment step fails in `before_feature` and `after_feature`
- Configure minimal Appium-Python-Client version to 2.3.0 to avoid import errors

v3.0.1
------

*Release date: 2023-05-09*

- Allow to search in `context.storage` using `[CONTEXT:a.b.c]` replacement when `before_feature` method is not used
- Execute after scenario methods also when a scenario is skipped to assure that scenario preconditions are cleaned
- Fix `[LANG:key]` replacement bug when it contains carriage returns
- `context.storage` must be initialized before dynamic environment steps in `before_scenario` method
- Fix error in Python 3.11 executing nose2 tests

v3.0.0
------

*Release date: 2023-05-03*

- Add support for Python 3.11
- Add support for Selenium 4
- Add support for Appium-Python-Client 2
- Visual testing comparison has changed

   | It only needs PIL library to compare images and generate the differences images
   | Old PerceptualDiff and Magick engines have been removed
   | Config property `engine` in [VisualTests] section has been removed
   | Images distance calculation method has changed, it is recommended to review thresholds in tests

- Now `gecko_driver_path`, `chrome_driver_path`, `explorer_driver_path` and `edge_driver_path` config properties
  in [Driver] section are optional, due to new SeleniumManager feature, that downloads drivers automatically
- New optional config property `safari_driver_path` in [Driver] section to configure Safari driver
- New optional config property `options` in [Chrome] section to configure Chrome options instead of using old
  property `goog:chromeOptions` in [Capabilities] section.
- New optional config property `base_path` in [Server] section to allow using old Selenium 3 or Appium 1 remote servers
- Remove support for lettuce tests
- Remove deprecated parameter `context` from `map_param` and POEditor methods
- Remove deprecated config property `restart_driver_fail` in [Driver] section
- Remove deprecated environment variables `Section_option`, `Config_environment` and `env`
- Update `[RANDOM_PHONE_NUMBER]` replacement using new `DataGenerator` class
- Update `[CONTEXT:a.b.c]` replacement to search data in context, context.storage and context.feature_storage
- Update `[CONTEXT:a.b.c]` replacement to allow dictionaries or classes in context fields

v2.7.0
------

*Release date: 2023-02-24*

- Fix drivers not being closed in `after_feature` when errors occur during `before_feature` steps execution
- Allow to add extensions to chrome options from properties file

   New config section [ChromeExtensions] with extensions file paths, e.g. 'firebug: resources/firebug-lite.crx'

v2.6.3
------

*Release date: 2022-12-09*

- Fix error in Android automatic context selection when context does not contain pages
- Remove Python 3.6 support (Python 3.6 reached the end of its life on December 23th, 2021)

v2.6.2
------

*Release date: 2022-10-18*

- New param [UUID] in *replace_param* method to generate a v4 UUID
- Improve POEditor error message when there are more than one project

v2.6.1
------

*Release date: 2022-06-28*

- Reference dotted keys when saving objects in context storage using [CONTEXT:a.b.c] formula
- Fix Visual testing image size for MacOS Retina and mobile layout

v2.6.0
------

*Release date: 2022-04-29*

- Update map_param method to allow recursive replacements
- Update replace_param function to allow multiple date expressions in the same param
- Fix error message to show parent locator instead of object reference when an element is not found
- Update replace_param function to allow NOW datetime expressions with arbitrary formats accepted by datetime.strftime

v2.5.0
------

*Release date: 2022-03-16*

- Update map_param method to use dataset global variables instead of context parameter
- Dataset variables needed for TOOLIUM, CONTEXT and POE replacements are set automatically
- Make POEditor methods independent of behave context
- Fix POEditor bug writing to file when terms contain slashes: from 'http:\/\/www.example.com' to 'http://www.example.com'

v2.4.0
------

*Release date: 2022-03-04*

- Add set_file_path and set_base64_path functions to dataset module, to set base paths for FILE and BASE64 mappings
- Visual testing baseline images are copied to output folder to facilitate report visualization in Jenkins
- Visual testing output folder is copied to *latest* folder to allow HTML Publisher Jenkins plugin to publish it
- Fix detection of POEditor configuration not available
- Fix indent error in Driver Configuration documentation

v2.3.0
------

*Release date: 2022-02-03*

- Add missing param in download_videos method to fix error downloading videos from a remote server
- Add map_param function to dataset module
- New param [RANDOM_PHONE_NUMBER] in *replace_param* method to generate random phone number

v2.2.1
------

*Release date: 2022-01-11*

- Add support for Python 3.10
- Add support for Appium-Python-Client 1.3.0
- Remove Python 3.5 support (Python 3.5 reached the end of its life on September 13th, 2020)
- Move code quality check from codacy to codeclimate
- Upgrade Sphinx version from 3.* to 4.* to fix doc compilation errors in readthedocs

v2.2.0
------

*Release date: 2021-11-03*

- Add JSON object/list conversion to Python dict/list in the type inference logic of the *replace_param* function
- Add *finalize_properties_configuration* method in *DriverWrapper* class to allow the modification of config properties
  upon initialization programmatically before driver creation
- Properties values configured by properties files can be overridden with system properties named
  *TOOLIUM_[SECTION]_[OPTION]*, moreover these system properties can be used to add new properties that do not exist in
  properties files
- Configuration system properties have been renamed. The old property names are deprecated but they can still be used.

   | Deprecated property name -> New property name
   | Config_environment -> TOOLIUM_CONFIG_ENVIRONMENT
   | Output_directory -> TOOLIUM_OUTPUT_DIRECTORY
   | Output_log_filename -> TOOLIUM_OUTPUT_LOG_FILENAME
   | Config_directory -> TOOLIUM_CONFIG_DIRECTORY
   | Config_log_filename -> TOOLIUM_CONFIG_LOG_FILENAME
   | Config_prop_filenames -> TOOLIUM_CONFIG_PROPERTIES_FILENAMES
   | Visual_baseline_directory -> TOOLIUM_VISUAL_BASELINE_DIRECTORY

- Behave user property 'Config_environment' is deprecated, use 'TOOLIUM_CONFIG_ENVIRONMENT' instead:

.. code:: console

    $ behave -D TOOLIUM_CONFIG_ENVIRONMENT=android

v2.1.1
------

*Release date: 2021-09-22*

- Avoid to overwrite parent in group elements when a custom parent is defined
- Fix Chrome options to allow to configure them at the same time in *Chrome* sections and in *goog:chromeOptions*
  capability

v2.1.0
------

*Release date: 2021-07-05*

- Add type inference and improve replacement logic in *replace_param* function
- Remove *generate_fixed_length_param* function, as all possible transformations are available in *replace_param*
- Fix docutils development dependency to version 0.16
- Fix InputText element class getting the text value for mobile apps in webview mode

v2.0.0
------

*Release date: 2021-06-15*

- Remove Python 2.7, 3.3 and 3.4 support
- Update deprecated methods to fix warnings in python3 execution
- Move *get_valid_filename* and *makedirs_safe* methods from *toolium.path_utils* to *toolium.utils.path_utils*
- Move *Utils* class from *toolium.utils* to *toolium.utils.driver_utils*
- Fix report when an error happens in the Dynamic Environment
- New param [TIMESTAMP] in *replace_param* method to generate timestamp value of the actual moment

v1.9.2
------

*Release date: 2021-04-09*

- Fix error in *deepcopy* method of *ExtendedConfigParser* class when two config properties have colon in name

v1.9.1
------

*Release date: 2021-03-11*

- Added new method wait_until_ajax_request_completed to driver utils class
- Move CI from Travis to Github Actions
- Fix string conversion in dataset utilities
- Add upper/lower conversion to replace param method

v1.9.0
------

*Release date: 2021-03-02*

- Added utilities to download files
- Get text for InputText element in mobile tests
- Add *translate_config_variables* method to *ExtendedConfigParser* class to translate config variables in a string
- Add dataset utilities
- Manage multiples webviews for mobile tests

v1.8.2
------

*Release date: 2020-12-17*

- Add support for python 3.9
- Add *get_driver_name* method to driver utils class
- Add doc about how to configure Firefox device mode
- Fix driver log types documentation

v1.8.1
------

*Release date: 2020-11-02*

- Create logs folder before downloading driver logs
- Add *set_focus* method to common elements and input text elements
- Fix driver log types list in local executions
- Fix automatic_context_selection for group element

v1.8.0
------

*Release date: 2020-10-05*

- Allow lists in config properties instead of converting them to strings
- Fix typo in documentation for configuration Server log types
- Include click action in InputText element
- New config property 'automatic_context_selection' in [Driver] section for mobile tests with webview

   | If it's false, the WebElement is searched using always NATIVE context
   | If it's true, the WebElement is searched using context NATIVE or WEBVIEW depeding of the webview attribute value

v1.7.2
------

*Release date: 2020-09-01*

- Move utils.py and path_utils.py files to utils folder maintaining backwards compatibility
- Fix input text when element has a shadowroot and text contains quotation marks
- New config property 'log_types' in [Server] section to configure webdriver log types that should be downloaded

v1.7.1
------

*Release date: 2020-05-18*

- Fix Appium dependency conflict, current allowed versions: from 0.24 to 0.52

v1.7.0
------

*Release date: 2020-05-11*

- Fix to allow step's text (context.text) declaration into dynamic environment sections
- Add `ssl` config property in [Server] section to allow using https in Selenium Grid url
- Visual testing comparison must fail when baseline does not exist and save mode is disabled
- Update dynamic environment behaviour to work as the behave's one, i.e. after scenario/feature actions are executed
  even when before scenario/feature actions fail
- Fix unit tests to work without any additional dependencies

v1.6.1
------

*Release date: 2020-01-21*

- Fix concurrent folder creation. Add *makedirs_safe* method to create a new folder.

v1.6.0
------

*Release date: 2020-01-15*

- New config property 'binary' in [Chrome] section to configure the chrome binary path
- Allow configuration properties with colon in name

    For instance, to set a capability with : in name, like:

.. code:: console

    goog:loggingPrefs = "{'performance': 'ALL', 'browser': 'ALL', 'driver': 'ALL'}"

    Following property should be added in properties.cfg:

.. code:: console

    [Capabilities]
    goog___loggingPrefs: {'performance': 'ALL', 'browser': 'ALL', 'driver': 'ALL'}

- Add support for python 3.8

v1.5.6
------

*Release date: 2019-10-04*

- Fix dynamic environment exit code when there are hook errors

v1.5.5
------

*Release date: 2019-07-29*

- Fix screeninfo dependency to 0.3.1 version

v1.5.4
------

*Release date: 2019-07-22*

- Add support to encapsulated elements (Shadowroot)

    | Only support CSS_SELECTOR locator
    | Input text page element fixed
    | It is not supported for list of elements yet
    | It is not supported for element find by parent yet
    | It is not supported nested encapsulation yet

- Fix Selenium dependency conflict

v1.5.3
------

*Release date: 2019-04-05*

- Fix error executing Appium locally

v1.5.2
------

*Release date: 2019-04-01*

- Check if a GGR session (current) is still active
- Download Selenoid logs files also when test fails
- Fix utils.py wait functions' descriptions
- Add new wait to utils.py in order to wait for an element not containing some text

v1.5.1
------

*Release date: 2019-03-18*

- Download Selenoid video and logs files only in linux nodes if video or logs are enabled
- Add a sleep between Selenoid retries when downloading files
- Manage exceptions in dynamic environment to mark affected scenarios as failed

v1.5.0
------

*Release date: 2019-02-26*

- Latest version of Appium can be used
- Make Toolium compatible with GGR and Selenoid
- Download execution video and session logs if the test fails using GGR and Selenoid
- Add logs path in the `_output` folder to download GGR logs
- Add `username` and `password` config properties in [Server] section to enable basic authentication in Selenium Grid (required by GGR)

v1.4.3
------

*Release date: 2018-12-18*

- Fix Appium version to 0.31 or minor

v1.4.2
------

*Release date: 2018-10-26*

- Add movement in X axis in *scroll_element_into_view* method
- Fix bugs and new features in the Dynamic Environment library:

   | chars no utf-8 are accepted
   | no replace behave prefixes into a step
   | pretty print by console, in Steps multi lines
   | raise an exception in error case
   | allow comments in the steps

- Add support for python 3.7

v1.4.1
------

*Release date: 2018-02-26*

- Fix README.rst format to be compatible with pypi
- Fix `after_scenario` error when toolium `before_feature` is not used
- Read `Config_environment` before properties initialization to read right properties file
- New config section [FirefoxArguments] to set firefox arguments from properties file, e.g. '-private'
- Add a config property `headless` in [Driver] section to enable headless mode in firefox and chrome
- New config properties 'monitor', 'bounds_x' and 'bounds_y' in [Driver] section to configure browser bounds and monitor
- Normalize filenames to avoid errors with invalid characters

v1.4.0
------

*Release date: 2018-02-04*

- Add pytest fixtures to start and stop drivers
- New config property `reuse_driver_session` in [Driver] section to use the same driver in all tests
- Rename config property `restart_driver_fail` in [Driver] section to `restart_driver_after_failure`
- Add @no_driver feature or scenario tag to do not start the driver in these tests
- Fix output folder names when driver type is empty
- Fix output log name when `Config_environment` is used
- Fix Chrome options using remote drivers with Selenium >= 3.6.0

v1.3.0
------

*Release date: 2017-09-12*

- Add Behave dynamic environment (more info in `Docs <http://toolium.readthedocs.io/en/latest/bdd_integration.html#behave-dynamic-environment>`_)
- Fix visual screenshot filename error when behave feature name contains :
- Add a config property 'explicitly_wait' in [Driver] section to set the default timeout used in *wait_until* methods
- When reuse_driver is true using behave, driver is initialized in *before_feature* method and closed in *after_feature*
  method
- Add @reuse_driver feature tag to reuse driver in a behave feature, even if reuse_driver is false
- Add @reset_driver scenario tag to restart driver before a behave scenario, even if reuse_driver is true
- Add *is_present* and *is_visible* methods to PageElement classes to know if an element is present or visible

v1.2.5
------

*Release date: 2017-03-24*

- Fix firefox initialization error using Selenium 2.X
- Add *wait_until_loaded* method to PageObject class to wait until all page elements with wait=True are visible

v1.2.4
------

*Release date: 2017-03-17*

- Fix NoSuchElementException error finding elements in nested groups

v1.2.3
------

*Release date: 2017-03-10*

- Save *geckodriver.log* file in output folder
- Fix MagickEngine name error when using an old version of needle
- Add *wait_until_clickable* method to Utils and PageElement classes to search for an element and wait until it is
  clickable

v1.2.2
------

*Release date: 2017-02-01*

- Fix error comparing screenshots in mobile tests
- Fix image size when enlarging a vertical image in visual testing reports
- Move js and css out of visual html report to avoid CSP errors

v1.2.1
------

*Release date: 2017-01-18*

- Fix error installing Toolium when setuptools version is too old

v1.2.0
------

*Release date: 2017-01-17*

- Refactored reset_object method. Now it has an optional parameter with the driver_wrapper.
- Fix error reading geckodriver logs after test failure
- Fix error downloading videos after failed tests
- Fix error in visual tests when excluding elements in a scrolled page
- New config property 'logs_enabled' in [Server] section to download webdriver logs even if the test passes
- New config property 'save_web_element' in [Driver] section

   | If it's false, the WebElement is searched whenever is needed (default value)
   | If it's true, the WebElement is saved in PageElement to avoid searching for the same element multiple times. Useful
     in mobile testing when searching for an element can take a long time.

- New config property 'restart_driver_fail' in [Driver] section to restart the driver when the test fails even though
  the value of *reuse_driver* property is *true*
- System property 'Config_environment' is used to select config files, e.g., to read android-properties.cfg file:

.. code:: console

    $ Config_environment=android nose2 web/tests/test_web.py

- Behave user property 'env' is deprecated, use 'Config_environment' instead:

.. code:: console

    $ behave -D Config_environment=android

v1.1.3
------

*Release date: 2016-11-18*

- Video download works in Selenium Grid 3
- New config property 'binary' in [Firefox] section to configure the firefox binary path
- Allow to configure visual baseline directory in ConfigFiles class (default: output/visualtests/baseline)
- Delete IE and Edge cookies after tests
- Fix wait_until_element_visible and wait_until_element_not_visible methods when the page element has a parent element
- Add *imagemagick* as visual engine to have better diff images

v1.1.2
------

*Release date: 2016-07-19*

- Baseline name property can contain *{Version}* to add actual version capability value to the baseline name
- New config property 'gecko_driver_path' in [Browser] section to configure the Gecko/Marionette driver location

v1.1.1
------

*Release date: 2016-06-30*

- Save webdriver logs of each driver, not just the first one, and only if test fails

v1.1.0
------

*Release date: 2016-06-03*

- New MobilePageObject class to test Android and iOS apps with the same base page objects
- Fix visual report links in Windows
- Add @no_reset_app, @reset_app and @full_reset_app behave tags to configure Appium reset capabilities for one scenario
- Add @android_only and @ios_only behave tags to exclude one scenario from iOS or Android executions
- Add a behave user property named *env* to select config files, e.g., to use android-properties.cfg file:

.. code:: console

    $ behave -D env=android

v1.0.1
------

*Release date: 2016-05-09*

- Fix wait_until_first_element_is_found error when element is None
- Fix app_strings initialization in page objects
- Fix swipe method to work with Appium 1.5 swipe

v1.0.0
------

*Release date: 2016-04-12*

DRIVER

- Refactor to move config property 'browser' in [Browser] section to 'type' property in [Driver] section
- Allow to run API tests with behave: driver type property must be empty
- Refactor to rename 'driver_path' config properties to 'chrome_driver_path', 'explorer_driver_path',
  'edge_driver_path', 'opera_driver_path' and 'phantomjs_driver_path'
- Refactor to move config properties 'reuse_driver' and 'implicitly_wait' from [Common] section to [Driver] section
- Add a new config property 'appium_app_strings' in [Driver] section to request app strings before each Appium test
- Add new config properties 'window_width' and 'window_height' in [Driver] section to configure browser window size
- Upload the error screenshot to Jira if the test fails
- Allow to add extensions to firefox profile from properties file

   New config section [FirefoxExtensions] with extensions file paths, e.g. 'firebug = firebug-3.0.0-beta.3.xpi'

- Allow to use a predefined firefox profile

   New config property 'profile' in [Firefox] section to configure the profile directory

- Allow to set chrome arguments from properties file

   New config section [ChromeArguments] with chrome arguments, e.g. 'lang = es'

PAGE OBJECTS

- Save WebElement in PageElement to avoid searching for the same element multiple times
- Refactor to rename get_element to get_web_element in Utils class and element to web_element in PageElement class
- Add *wait_until_first_element_is_found* method to Utils class to search for a list of elements and wait until one of
  them is found
- Add new page element types: Checkbox, InputRadio, Link, Group and PageElements

BEHAVE

- Allow to modify Toolium properties from behave userdata configuration, e.g.:

.. code:: console

    $ behave -D Driver_type=chrome

VISUAL TESTING

- Refactor to rename assertScreenshot to assert_screenshot and assertFullScreenshot to assert_full_screenshot
- Add force parameter to *assert_screenshot* methods to compare the screenshot even if visual testing is disabled by
  configuration. If the assertion fails, the test fails.
- Baseline name property can contain *{PlatformVersion}* or *{RemoteNode}* to add actual platform version or remote
  node name to the baseline name


v0.12.1
-------

*Release date: 2016-01-07*

- Fix app_strings initialization in Behave Appium tests
- In Behave tests, Toolium config is saved in context.toolium_config instead of using context.config to avoid
  overriding Behave config

v0.12.0
-------

*Release date: 2015-12-23*

- Allow to create a second driver using DriverWrapper constructor:

.. code-block:: python

    second_wrapper = DriverWrapper()
    second_wrapper.connect()

- Fix page object issue with non-default driver. Now page object and utils init methods have both a driver_wrapper
  optional parameter instead of driver parameter.
- Fix swipe over an element in Android and iOS web tests
- Move set_config_* and set_output_* test case methods to ConfigFiles class
- Add behave environment file to initialize Toolium wrapper from behave tests

v0.11.3
-------

*Release date: 2015-11-24*

- Fix image size in visual testing for Android and iOS web tests
- Baseline name property allows any configuration property value to configure the visual testing baseline folder, e.g.:

   | {AppiumCapabilities_deviceName}-{AppiumCapabilities_platformVersion}: this baseline_name could use baselines as iPhone_6-8.3, iPhone_6-9.1, iPhone_6s-9.1, ...
   | {Browser_browser}: this baseline_name could use baselines as firefox, iexplore, ... (default value)

- Fix page elements initialization when they are defined outside of a page object

v0.11.2
-------

*Release date: 2015-11-11*

- Compatibility with Python 3

v0.11.1
-------

*Release date: 2015-11-02*

- New config property 'operadriver_path' in [Browser] section to configure the Opera Driver location
- Fix initialization error when a page object contains another page object
- Fix visual testing error if browser is phantomjs
- Fix firefox profile error in remote executions
- Configure setup.py to execute tests with 'python setup.py test'
- Convert markdown (.md) files to reStructuredText (.rst) and update long_description with README.rst content

v0.11.0
-------

*Release date: 2015-10-21*

- Rename library from seleniumtid to toolium
- Distributed under Apache Software License, Version 2

v0.10.0
-------

*Release date: 2015-09-23*

- Add support to Edge Windows browser
- New config property 'summary_prefix' in [Jira] section to modify default TCE summary
- Add scroll_element_into_view method to PageElement that scroll to element
- Add parent parameter to PageElement when element must be found from parent
- Page elements can be defined as class attributes, it is no longer necessary to define them as instance attributes in
  init_page_elements()
- Add wait_until_visible, wait_until_not_visible and assertScreenshot methods to PageElement
- Allow to set Chrome mobile options from properties file

   New config section [ChromeMobileEmulation] with mobile emulation options, e.g. 'deviceName = Google Nexus 5'

- Configuration system properties have been renamed

   | Old properties: Files_output_path, Files_log_filename, Files_properties, Files_logging
   | New properties: Output_directory, Output_log_filename, Config_directory, Config_prop_filenames, Config_log_filename

- Add set_config_* and set_output_* test case methods to configure output and config files instead of using
  configuration system properties

v0.9.3
------

*Release date: 2015-07-24*

- Allow to set custom driver capabilities from properties file

   New config section [Capabilities] with driver capabilities

- Fix set_value and app_strings errors in mobile web tests
- Fix set_value error in iOS tests when using needle

v0.9.2
------

*Release date: 2015-06-02*

- Allow to find elements by ios_uiautomation in visual assertions
- Fix app_strings error in mobile web tests
- Use set_value instead of send_keys to run tests faster

v0.9.1
------

*Release date: 2015-05-21*

- Add swipe method in Utils to allow swipe over an element
- Only one property file is mandatory if *Files_properties* has multiple values
- Allow to exclude elements from visual screenshots

v0.9.0
------

*Release date: 2015-05-12*

- Output path (screenshots, videos, visualtests) can be specified with a system property: *Files_output_path*
- Update app_strings in Appium tests only if the driver has changed
- Move visual properties from [Server] section to [VisualTests] section
- With a visual assertion error, the test can fail or give an error message and continue

   New config property 'fail' in [VisualTests] section to fail the test when there is a visual error

- Create a html report with the visual tests results

   New config property 'complete_report' in [VisualTests] section to include also correct visual assertions in report

- Configure multiple baseline name for different browsers, languages and versions

   | New config property 'baseline_name' in [VisualTests] section to configure the name of the baseline folder
   | Allow {browser}, {language} and {platformVersion} variables, e.g. baseline_name = {browser}-{language}
   | The default baseline_name is {browser}.

- Add assertFullScreenshot method in SeleniumTestCase

v0.8.6
------

*Release date: 2015-04-17*

- Add wait_until_element_visible method in utils class
- Logger filename can be specified with a system property: *Files_log_filename*

v0.8.5
------

*Release date: 2015-03-23*

- Add Button page element
- AppiumTestCase has a new attribute app_strings, a dict with application strings in the active language

v0.8.4
------

*Release date: 2015-03-05*

- Allow to set firefox and chrome preferences from properties file

   | New config section [FirefoxPreferences] with firefox preferences, e.g. 'browser.download.dir = /tmp'
   | New config section [ChromePreferences] with chrome preferences, e.g. 'download.default_directory = /tmp'

v0.8.3
------

*Release date: 2015-02-11*

- Read properties file before each test to allow executing tests with different configurations (android, iphone, ...)

v0.8.2
------

*Release date: 2015-02-04*

- Logging and properties config files can be specified with a system property: *Files_logging* and *Files_properties*

   *Files_properties* allows multiple files separated by ;

v0.8.1
------

*Release date: 2015-01-26*

- Fixed minor bugs
- Add visual testing to lettuce tests

v0.8
----

*Release date: 2015-01-20*

- Add visual testing to SeleniumTestCase and AppiumTestCase

   | New config property 'visualtests_enabled' in [Server] section to enable visual testing
   | New config property 'visualtests_save' in [Server] section to overwrite baseline images with actual screenshots
   | New config property 'visualtests_engine' in [Server] section to select image engine (pil or perceptualdiff)

v0.7
----

*Release date: 2014-12-23*

- Allow to autocomplete self.driver and self.utils in IDEs
- Remove non-mandatory requirements

v0.6
----

*Release date: 2014-12-05*

- Multiple tests of a class can be linked to the same Jira Test Case
- If test fails, the error message will be added as a comment to the Jira Test Case Execution
- Update Jira Test Cases also in lettuce tests

v0.5
----

*Release date: 2014-12-01*

- Downloads the saved video if the test has been executed in a VideoGrid
- Add BasicTestCase class to be used in Api tests or in other tests without selenium driver

v0.4
----

*Release date: 2014-11-12*

- Add Lettuce terrain file to initialize Selenium driver
- Add ConfigDriver.create_driver method to create a new driver with specific configuration
- Add wait_until_element_not_visible method in utils class

v0.3
----

*Release date: 2014-06-12*

- Add a config property 'implicitly_wait' in [Common] section to set an implicit timeout
- Add a config property 'reuse_driver' in [Common] section to use the same driver in all tests of each class
- The driver can be reused only in a test class setting a class variable 'reuse_driver = True'

v0.2
----

*Release date: 2014-05-13*

- Now depends on Appium 1.0

v0.1
----

*Release date: 2014-03-04*

- First version of the selenium library in python
