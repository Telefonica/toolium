.. _browser_configuration:

Browser Configuration
=====================

Common Configuration
--------------------

To choose the browser in which Selenium will execute the tests, configure *browser* property in *[Browser]* section in
properties.cfg file with one of these values: firefox, chrome, iexplore, edge, safari, opera or phantomjs.

The following example shows how to choose Firefox::

    [Browser]
    browser: firefox

By default, the browser is maximized. To define a different window size, configure *window_width* and *window_height*
properties in *[Browser]* section::

    [Browser]
    window_width: 1024
    window_height: 768

Mandatory Configuration
-----------------------

Besides selecting the browser, some specific configuration is needed when running locally.

Firefox
~~~~~~~

- No extra configuration is needed ::

    [Browser]
    browser: firefox

Chrome
~~~~~~

- Download `chromedriver_*.zip <http://chromedriver.storage.googleapis.com/index.html>`_
- Unzip file and save the executable in a local folder
- Configure driver path in *[Browser]* section in properties.cfg file ::

    [Browser]
    browser: chrome
    chromedriver_path: C:\Drivers\chromedriver.exe

Internet Explorer
~~~~~~~~~~~~~~~~~

- Download `IEDriverServer_Win32_*.zip <http://selenium-release.storage.googleapis.com/index.html>`_
- It's recommended to use Win32 version, because x64 version is very slow
- Unzip file and save the executable in a local folder
- Configure driver path in *[Browser]* section in properties.cfg file ::

    [Browser]
    browser: iexplore
    explorerdriver_path: C:\Drivers\IEDriverServer.exe

Edge
~~~~

- Download `MicrosoftWebDriver.msi <https://www.microsoft.com/en-us/download/details.aspx?id=48212>`_
- Install MicrosoftWebDriver.msi
- Configure driver path in *[Browser]* section in properties.cfg file ::

    [Browser]
    browser: edge
    edgedriver_path: C:\Drivers\MicrosoftWebDriver.exe

Safari
~~~~~~

- Download `SafariDriver.safariextz <http://selenium-release.storage.googleapis.com/index.html>`_
- Open file in Safari and install it ::

    [Browser]
    browser: safari

Opera
~~~~~

- Download `operadriver_*.zip <https://github.com/operasoftware/operachromiumdriver/releases>`_
- Unzip file and save the executable in a local folder
- Configure driver path in *[Browser]* section in properties.cfg file ::

    [Browser]
    browser: opera
    operadriver_path: C:\Drivers\operadriver.exe

PhantomJS
~~~~~~~~~

- Download `phantomjs-*.zip <http://phantomjs.org/download.html>`_
- Unzip file and save the executable in a local folder
- Configure driver path in *[Browser]* section in properties.cfg file ::

    [Browser]
    browser: phantomjs
    phantomdriver_path: C:\Drivers\phantomjs.exe

Additional Configuration
------------------------

Firefox
~~~~~~~

To use a custom Firefox profile, create a *[FirefoxPreferences]* configuration section and add every preference that
you want to configure with its value.

For example, the following configuration allows to download files without asking user::

    [Browser]
    browser: firefox

    [FirefoxPreferences]
    browser.download.folderList: 2
    browser.download.dir: C:\tmp
    browser.helperApps.neverAsk.saveToDisk: application/octet-stream
    dom.serviceWorkers.enabled: True

Firefox plugins can also be installed adding their file paths to *[FirefoxExtensions]* configuration section.

For example, the following configuration exports network information to har files::

    [Browser]
    browser: firefox

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

To use a predefined firefox profile, configure the profile directory in *[Firefox]* configuration section::

    [Firefox]
    profile: resources/firefox-profile.default


Chrome
~~~~~~

To configure Chrome preferences, create a *[ChromePreferences]* configuration section and add every preference that
you want to configure with its value.

For example, the following configuration allows to download files without asking user::

    [Browser]
    browser: chrome

    [ChromePreferences]
    download.default_directory: C:\tmp

Another examples showing how to use Chrome Device Mode in two different ways::

    [Browser]
    browser: chrome

    [ChromeMobileEmulation]
    deviceName: Google Nexus 5

::

    [Browser]
    browser: chrome

    [ChromeMobileEmulation]
    deviceMetrics: { "width": 360, "height": 640, "pixelRatio": 3.0 }
    userAgent: Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko)
               Chrome/18.0.1025.166 Mobile Safari/535.19
