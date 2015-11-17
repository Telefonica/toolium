Browser Configuration
=====================

Configure browser property in [Browser] section of properties.cfg file with one of the valid values: firefox, chrome,
iexplore, edge, safari, opera, phantomjs, iphone, android. ::

    [Browser]
    browser: firefox

Firefox
~~~~~~~

- No extra configuration is needed

Chrome
~~~~~~

- Download `chromedriver_*.zip <http://chromedriver.storage.googleapis.com/index.html>`_
- Unzip file and save the executable in a local folder
- Configure driver path in [Browser] section of properties.cfg file ::

    [Browser]
    chromedriver_path: C:\Drivers\chromedriver.exe

Internet Explorer
~~~~~~~~~~~~~~~~~

- Download `IEDriverServer_Win32_*.zip <http://selenium-release.storage.googleapis.com/index.html>`_
- It's recommended to use Win32 version, because x64 version is very slow
- Unzip file and save the executable in a local folder
- Configure driver path in [Browser] section of properties.cfg file ::

    [Browser]
    explorerdriver_path: C:\Drivers\IEDriverServer.exe

Edge
~~~~

- Download `MicrosoftWebDriver.msi <https://www.microsoft.com/en-us/download/details.aspx?id=48212>`_
- Install MicrosoftWebDriver.msi
- Configure driver path in [Browser] section of properties.cfg file ::

    [Browser]
    edgedriver_path: C:\Drivers\MicrosoftWebDriver.exe

Safari
~~~~~~

- Download `SafariDriver.safariextz <http://selenium-release.storage.googleapis.com/index.html>`_
- Open file in Safari and install it

Opera
~~~~~

- Download `operadriver_*.zip <https://github.com/operasoftware/operachromiumdriver/releases>`_
- Unzip file and save the executable in a local folder
- Configure driver path in [Browser] section of properties.cfg file ::

    [Browser]
    operadriver_path: C:\Drivers\operadriver.exe

PhantomJS
~~~~~~~~~

- Download `phantomjs-*.zip <http://phantomjs.org/download.html>`_
- Unzip file and save the executable in a local folder
- Configure driver path in [Browser] section of properties.cfg file ::

    [Browser]
    phantomdriver_path: C:\Drivers\phantomjs.exe
