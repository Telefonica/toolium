.. _browser_configuration:

Browser Configuration
=====================

Common Configuration
--------------------

To choose the browser in which Selenium or Playwright will execute the tests, configure *type* property in *[Driver]*
section in properties.cfg file with one of these values: firefox, chrome, iexplore, edge or safari.

The following example shows how to choose Firefox::

    [Driver]
    type: firefox

By default, the browser is maximized. To define a different window size, configure *window_width* and *window_height*
properties in *[Driver]* section::

    [Driver]
    window_width: 1024
    window_height: 768

Additional Configuration
------------------------

To configure `Browser options <https://www.selenium.dev/documentation/webdriver/drivers/options/>`_, create a
*[Capabilities]* configuration section and add every option that you want to configure with its value.

For example, the following configuration changes page load strategy to eager mode::

    [Capabilities]
    pageLoadStrategy: eager

Firefox
~~~~~~~

**Firefox section**

To use a predefined firefox profile, configure the profile directory in *[Firefox]* configuration section::

    [Driver]
    type: firefox

    [Firefox]
    profile: resources/firefox-profile.default

When firefox is installed in a non-default location, configure the firefox binary path in *[Firefox]* configuration
section::

    [Driver]
    type: firefox

    [Firefox]
    binary: /usr/local/firefox_beta/firefox

**FirefoxPreferences section**

To configure Firefox preferences, create a *[FirefoxPreferences]* configuration section and add every preference that
you want to configure with its value.

For example, the following configuration allows to download files without asking user::

    [Driver]
    type: firefox

    [FirefoxPreferences]
    browser.download.folderList: 2
    browser.download.dir: C:\tmp
    browser.helperApps.neverAsk.saveToDisk: application/octet-stream
    dom.serviceWorkers.enabled: True

Another example showing how to use *Firefox Device Mode*::

    [Driver]
    type: firefox
    window_width: 1200
    window_height: 800

    [FirefoxPreferences]
    general.useragent.override: Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19

**FirefoxExtensions section**

Firefox plugins can also be installed adding their file paths to *[FirefoxExtensions]* configuration section.

For example, the following configuration exports network information to har files::

    [Driver]
    type: firefox

    [FirefoxPreferences]
    devtools.netmonitor.har.enableAutoExportToFile: True
    devtools.netmonitor.har.defaultLogDir: /tmp/har
    devtools.netmonitor.har.forceExport: False
    devtools.netmonitor.har.pageLoadedTimeout: 10
    extensions.netmonitor.har.enableAutomation: True
    extensions.netmonitor.har.autoConnect: True
    devtools.netmonitor.har.defaultFileName: network-test

    [FirefoxExtensions]
    firebug: resources/firebug-3.0.0-beta.3.xpi

**FirefoxArguments section**

To configure `Firefox arguments <https://developer.mozilla.org/en-US/docs/Mozilla/Command_Line_Options#Browser>`_, create a
*[FirefoxArguments]* configuration section and add every argument that you want to configure with its value.

For example, to open firefox in a private browsing mode::

    [Driver]
    type: firefox

    [FirefoxArguments]
    -private:

Chrome
~~~~~~

**ChromePreferences section**

To configure `Chrome preferences <https://cs.chromium.org/chromium/src/chrome/common/pref_names.cc>`_, create a
*[ChromePreferences]* configuration section and add every preference that you want to configure with its value.

For example, the following configuration allows to download files without asking user::

    [Driver]
    type: chrome

    [ChromePreferences]
    download.default_directory: C:\tmp

**ChromeArguments section**

To configure `Chrome arguments <https://cs.chromium.org/chromium/src/chrome/common/chrome_switches.cc>`_, create a
*[ChromeArguments]* configuration section and add every argument that you want to configure with its value.

For example, to use a predefined chrome profile::

    [Driver]
    type: chrome

    [ChromeArguments]
    user-data-dir: C:\Users\USERNAME\AppData\Local\Google\Chrome\User Data

**ChromeExtensions section**

Chrome plugins can also be installed adding their file paths to *[ChromeExtensions]* configuration section.

For example, the following configuration install firebug lite extension in Chrome::

    [Driver]
    type: chrome

    [ChromeExtensions]
    firebug: resources/firebug-lite.crx

**ChromeMobileEmulation section**

Another examples showing how to use
`Chrome Device Mode <https://sites.google.com/a/chromium.org/chromedriver/mobile-emulation>`_ in two different ways::

    [Driver]
    type: chrome

    [ChromeMobileEmulation]
    deviceName: Google Nexus 5

::

    [Driver]
    type: chrome

    [ChromeMobileEmulation]
    deviceMetrics: { "width": 360, "height": 640, "pixelRatio": 3.0 }
    userAgent: Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19

**Capabilities section**

Take in account that some Chrome capabilities contain a colon in their name, for example *goog:loggingPrefs*. As colon
is not allowed in *ConfigParser* keys, it has been extended so they can be configured in *[Capabilities]* section
replacing ':' with '___' in the key name::

    [Capabilities]
    goog___loggingPrefs: {'performance': 'ALL', 'browser': 'ALL', 'driver': 'ALL'}

**Chrome section**

Additional `Chrome Options <https://chromedriver.chromium.org/capabilities#h.p_ID_102>`_ can be configured in
*[Chrome]* configuration section::

    [Driver]
    type: chrome

    [Chrome]
    options: {'excludeSwitches': ['enable-automation'], 'perfLoggingPrefs': {'enableNetwork': True}}

When Chrome is installed in a non-default location, configure the Chrome binary path in *[Chrome]* configuration
section::

    [Driver]
    type: chrome

    [Chrome]
    binary: /usr/local/chrome_beta/chrome

Driver Download
---------------

Since Selenium 4, Selenium Manager downloads automatically the corresponding browser driver, when running the tests
locally. But if it is still needed to be downloaded, just follow these instructions:

Firefox
~~~~~~~

- Download `geckodriver-*.zip <https://github.com/mozilla/geckodriver/releases>`_
- Unzip file and save the executable in a local folder
- Configure driver path in *[Driver]* section in properties.cfg file ::

    [Driver]
    type: firefox
    gecko_driver_path: C:\Drivers\geckodriver.exe

Chrome
~~~~~~

- Download `chromedriver_*.zip <http://chromedriver.storage.googleapis.com/index.html>`_
- Unzip file and save the executable in a local folder
- Configure driver path in *[Driver]* section in properties.cfg file ::

    [Driver]
    type: chrome
    chrome_driver_path: C:\Drivers\chromedriver.exe

Internet Explorer
~~~~~~~~~~~~~~~~~

- Download `IEDriverServer_Win32_*.zip <https://github.com/SeleniumHQ/selenium/releases>`_
- It's recommended to use Win32 version, because x64 version is very slow
- Unzip file and save the executable in a local folder
- Configure driver path in *[Driver]* section in properties.cfg file ::

    [Driver]
    type: iexplore
    explorer_driver_path: C:\Drivers\IEDriverServer.exe

Edge
~~~~

- Download `edgedriver_win64.zip <https://developer.microsoft.com/es-es/microsoft-edge/tools/webdriver/>`_
- Unzip file and save the executable in a local folder
- Configure driver path in *[Driver]* section in properties.cfg file ::

    [Driver]
    type: edge
    edge_driver_path: C:\Drivers\msedgedriver.exe

Safari
~~~~~~

- Configure driver path in *[Driver]* section in properties.cfg file ::

    [Driver]
    type: safari
    safari_driver_path: /usr/bin/safaridriver
