.. _browser_configuration:

Browser Configuration
=====================

Common Configuration
--------------------

To choose the browser in which Selenium will execute the tests, configure *type* property in *[Driver]* section in
properties.cfg file with one of these values: firefox, chrome, iexplore, edge, safari, opera or phantomjs.

The following example shows how to choose Firefox::

    [Driver]
    type: firefox

By default, the browser is maximized. To define a different window size, configure *window_width* and *window_height*
properties in *[Driver]* section::

    [Driver]
    window_width: 1024
    window_height: 768

Mandatory Configuration
-----------------------

Besides selecting the browser, some specific configuration is needed when running locally.

Firefox (with Selenium 3)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Download `geckodriver-*.zip <https://github.com/mozilla/geckodriver/releases>`_
- Unzip file and save the executable in a local folder
- Configure driver path in *[Driver]* section in properties.cfg file ::

    [Driver]
    type: firefox
    gecko_driver_path: C:\Drivers\geckodriver.exe

Firefox 48+ (with Selenium 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Download `geckodriver-*.zip <https://github.com/mozilla/geckodriver/releases>`_
- Unzip file and save the executable in a local folder
- Configure driver path in *[Driver]* section in properties.cfg file ::

    [Driver]
    type: firefox
    gecko_driver_path: C:\Drivers\geckodriver.exe

- Enable Gecko/Marionette driver in *[Capabilities]* section in properties.cfg file ::

    [Capabilities]
    marionette: true

Firefox 47 (with Selenium 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- No extra configuration is needed ::

    [Driver]
    type: firefox

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

- Download `IEDriverServer_Win32_*.zip <http://selenium-release.storage.googleapis.com/index.html>`_
- It's recommended to use Win32 version, because x64 version is very slow
- Unzip file and save the executable in a local folder
- Configure driver path in *[Driver]* section in properties.cfg file ::

    [Driver]
    type: iexplore
    explorer_driver_path: C:\Drivers\IEDriverServer.exe

Edge
~~~~

- Download `MicrosoftWebDriver.msi <https://www.microsoft.com/en-us/download/details.aspx?id=48212>`_
- Install MicrosoftWebDriver.msi
- Configure driver path in *[Driver]* section in properties.cfg file ::

    [Driver]
    type: edge
    edge_driver_path: C:\Drivers\MicrosoftWebDriver.exe

Safari
~~~~~~

- Download `SafariDriver.safariextz <http://selenium-release.storage.googleapis.com/index.html>`_
- Open file in Safari and install it ::

    [Driver]
    type: safari

Opera
~~~~~

- Download `operadriver_*.zip <https://github.com/operasoftware/operachromiumdriver/releases>`_
- Unzip file and save the executable in a local folder
- Configure driver path in *[Driver]* section in properties.cfg file ::

    [Driver]
    type: opera
    opera_driver_path: C:\Drivers\operadriver.exe

PhantomJS
~~~~~~~~~

- Download `phantomjs-*.zip <http://phantomjs.org/download.html>`_
- Unzip file and save the executable in a local folder
- Configure driver path in *[Driver]* section in properties.cfg file ::

    [Driver]
    type: phantomjs
    phantomjs_driver_path: C:\Drivers\phantomjs.exe

Additional Configuration
------------------------

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

To use a custom Firefox profile, create a *[FirefoxPreferences]* configuration section and add every preference that
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

**Chrome section**

When Chrome is installed in a non-default location, configure the Chrome binary path in *[Chrome]* configuration
section::

    [Driver]
    type: chrome

    [Chrome]
    binary: /usr/local/chrome_beta/chrome

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

