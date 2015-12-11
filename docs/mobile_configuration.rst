Mobile Configuration
====================

To choose mobile operating system in which Appium will execute the tests, configure *browser* property in *[Browser]*
section in properties.cfg file with one of these values: ios or android.

The following example shows how to choose Android::

    [Browser]
    browser: android


Moreover, configure Appium properties in *[AppiumCapabilities]* section in properties.cfg file. The following example
shows how to configure Appium to run tests over TestApp app on an iPhone 6 with iOS 8.3::

    [Browser]
    browser: ios

    [AppiumCapabilities]
    automationName: Appium
    platformName: iOS
    deviceName: iPhone 6
    platformVersion: 8.3
    app: http://server_url/TestApp.zip

See http://appium.io/slate/en/master#appium-server-capabilities for the complete Appium capabilities list.
