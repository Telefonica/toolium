APP             = selenium_tid_python
VERSION         ?= $(shell cat VERSION)
RELEASE         ?= $(shell git log --pretty=oneline | wc -l | tr -d ' ')
ARCH            = noarch
PACKAGE         = $(APP)-$(VERSION)-$(RELEASE).$(ARCH).rpm
ROOT            = $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PYTHON          ?= $(shell which python2.7)
MKD2PDF         ?= $(shell which markdown-pdf)
VIRTUALENV      ?= virtualenv
TEST            = tests
SPHINXBUILD     = sphinx-build
SPHINXSOURCEDIR = docs/src-docs/source
SPHINXBUILDDIR  = docs/src-docs/build

ifeq ($(USER), vagrant)
VENV_PREFIX = $(HOME)/.venv
TMP=/tmp
else
VENV_PREFIX = $(ROOT)/tmp/venv
TMP=$(ROOT)/tmp
endif

VENV = $(VENV_PREFIX)/$(APP)
REQ = requirements.txt

TESTREQ = requirements_dev.txt

ACCEPTANCE_TEST_VENV = $(VENV_PREFIX)/$(TEST)
ACCEPTANCE_TEST_REQ = test/acceptance/src/requirements.txt

UNIT_TEST_ARGS=--nocapture --verbosity=3 --stop --where tests
COVERAGE_ARGS=--with-coverage --cover-erase --cover-package=$(APP) \
               --cover-branches --with-xunit --cover-xml \
               --xunit-file=$(ROOT)/dist/nosetest.xml \
               --cover-xml-file=$(ROOT)/dist/coverage.xml

all: default

default:
	@echo
	@echo "Welcome to '$(APP)' software package:"
	@echo
	@echo "usage: make <command>"
	@echo
	@echo "commands:"
	@echo "    clean         - Remove generated files and directories"
	@echo "    venv          - Create and update virtual environments"
	@echo "    install       - Install application"
	@echo "    sdist         - Build a tar.gz software distribution of the package"
	@echo "    rpm           - Create $(PACKAGE) rpm"
	@echo "    docs          - Create package documentation"
	@echo "    egg           - Create python egg"
	@echo "    unittest      - Execute unit tests"
	@echo "    src-doc-html  - Build sphinx documentation"
	@echo "    coverage      - Execute unittests and code coverage"
	@echo "    pylint        - Run pylint"
	@echo

init:
	mkdir -p $(ROOT)/dist
	mkdir -p $(TMP)/rpmbuild/SOURCES
	mkdir -p $(TMP)/rpmbuild/BUILD
	mkdir -p $(TMP)/rpmbuild/RPMS

sdist:
	@echo ">>> Creating source distribution..."
	$(VENV)/bin/python2.7 setup.py sdist
	@echo ">>> OK. TGZ generated in $(ROOT)/dist"
	@echo

rpm: init sdist
	@echo ">>> Creating RPM package..."
	cp $(ROOT)/dist/$(APP)-$(VERSION).tar.gz $(TMP)/rpmbuild/SOURCES
	rpmbuild -bb $(APP).spec                                                 \
             --define "version $(VERSION)"                                   \
             --define "release $(RELEASE)"                                   \
             --define "arch $(ARCH)"                                         \
             --define "_target_os linux"                                     \
             --define "_topdir $(TMP)/rpmbuild"                              \
             --define "buildroot $(TMP)/rpmbuild/BUILDROOT"                  \
             --define "__python $(PYTHON)"                                   \
             --define "python_sitelib virtualenv/lib/python2.7/site-packages"      \
             --define "_sysconfdir /etc"                                     \
             --define "_bindir /usr/bin"                                     \
             --nodeps                                                        \
             --buildroot=$(TMP)/rpmbuild/BUILDROOT

	cp $(TMP)/rpmbuild/RPMS/$(ARCH)/$(PACKAGE) $(ROOT)/dist
	@echo ">>> OK. RPM generated in $(ROOT)/dist"
	@echo

venv: $(VENV)

$(VENV): $(REQ) $(TESTREQ)
	mkdir -p $@; \
	export GIT_SSL_NO_VERIFY=true; \
	$(VIRTUALENV) --no-site-packages --distribute -p $(PYTHON) $@; \
	$@/bin/pip install --upgrade -r $(REQ); \
	$@/bin/pip install --upgrade -r $(TESTREQ); \

unittest: init venv
	$(VENV)/bin/nosetests $(UNIT_TEST_ARGS)

coverage: init venv
	$(VENV)/bin/nosetests $(COVERAGE_ARGS) $(UNIT_TEST_ARGS)
	@echo ">>> OK. Coverage reports generated in $(ROOT)/dist"

docs:
ifneq "$(MKD2PDF)" ""
	@echo ">>> Creating documentation..." ; \
	mkdir -p dist ; \
	$(MKD2PDF) -s docstyle.css -o dist/README.pdf README.md; \
	echo ">>> OK. PDFs generated in $(ROOT)/dist" ;\
	echo
else
	@echo ">>> ERROR. markdown-pdf not found. Docs not generated" ;\
	echo
endif

# Just for development purposes. It uses your active python2.7
# Remember to update your requirements if needed
egg:
	$(PYTHON) setup.py bdist_egg

# Just for development purposes. It uses your active python2.7
# Remember to update your requirements if needed
install:
	$(PYTHON) setup.py install

src-doc-html: venv
	@echo ">>> Cleaning sphinx doc files..."
	rm -rf $(SPHINXBUILDDIR)/html
	@echo ">>> Generating doc files..."
	$(VENV)/bin/$(SPHINXBUILD) -b html $(SPHINXSOURCEDIR) $(SPHINXBUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(SPHINXBUILDDIR)/html."

pylint: init venv
	$(VENV)/bin/pylint  --rcfile=pylint.rc -f parseable iammy_analytics | tee dist/pylint.log
	$(VENV)/bin/pylint  --rcfile=pylint.rc -f parseable tests | tee dist/pylint.log
	@echo ">>> OK. Pylint reports generated in $(ROOT)/dist"

clean:
	@echo ">>> Cleaning temporal files..."
	rm -rf tmp/ dist/ *.egg-info/ build/
	@echo

.PHONY: all sdist rpm clean doc