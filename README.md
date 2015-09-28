Toolium
=======

*toolium* is a python library for testing api, web and mobile applications using requests, selenium and appium tools

Last version of this library can be installed with pip from internal artifactory:
```
pip install toolium -i http://artifactory.hi.inet/artifactory/api/pypi/pypi/simple
```

Requirements
------------

Python 2.7 (http://www.python.org)

Installation
------------

Configure a virtual environment with the required packages:

```
virtualenv ENV
source ENV/bin/activate
pip install -r requirements.txt
easy_install pillow
pip install -r requirements_dev.txt
```

The following packages will be installed:
  * requests (http://docs.python-requests.org)
  * selenium (http://docs.seleniumhq.org/)
  * Appium-Python-Client (https://github.com/appium/python-client)

Documentation
-------------

See toolium docs in http://quality/jenkins/job/toolium/docs/

Release notes: [CHANGELOG.md](/CHANGELOG.md)
