.. _mobile_configuration:

Mobile Configuration
====================

To choose mobile operating system in which Appium will execute the tests, configure *type* property in *[Driver]*
section in properties.cfg file with one of these values: :code:`ios` or :code:`android`. Moreover, configure Appium
properties in *[AppiumCapabilities]* section in properties.cfg file.

The following example shows how to configure Appium to run tests over TestApp app on an iPhone 14 with iOS 16.1::

    [Driver]
    type: ios

    [AppiumCapabilities]
    automationName: XCUITest
    platformName: iOS
    deviceName: iPhone 14
    platformVersion: 16.1
    app: http://server_url/TestApp.zip

And this example shows how to choose Android::

    [Driver]
    type: android

    [AppiumCapabilities]
    automationName: UiAutomator2
    platformName: Android
    deviceName: Android
    app: http://server_url/TestApp.apk

See https://appium.github.io/appium/docs/en/2.0/guides/caps/ for the complete Appium capabilities list.
