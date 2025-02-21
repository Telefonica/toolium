.. _mobile_configuration:

Mobile Configuration
====================

To choose mobile operating system in which Appium will execute the tests, configure :code:`type` property in
:code:`[Driver]` section in :code:`conf/properties.cfg` file with one of these values: :code:`ios` or :code:`android`.
Moreover, configure Appium properties in :code:`[AppiumCapabilities]` section in :code:`conf/properties.cfg` file.

The following example shows how to configure Appium to run tests over TestApp app on an iPhone 14 with iOS 16.1::

    [Driver]
    type: ios

    [Capabilities]
    platformName: iOS

    [AppiumCapabilities]
    automationName: XCUITest
    deviceName: iPhone 14
    platformVersion: 16.1
    app: http://server_url/TestApp.zip

And this example shows how to choose Android::

    [Driver]
    type: android

    [Capabilities]
    platformName: Android

    [AppiumCapabilities]
    automationName: UiAutomator2
    deviceName: Android
    app: http://server_url/TestApp.apk

See https://appium.github.io/appium/docs/en/2.0/guides/caps/ for the complete Appium capabilities list.
