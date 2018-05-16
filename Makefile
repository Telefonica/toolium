APP				= toolium
VERSION			?= $(shell cat VERSION)
RELEASE			?= $(shell git log --pretty=oneline | wc -l | tr -d ' ')
ARCH			= noarch
PACKAGE			= $(APP)-$(VERSION)-$(RELEASE).$(ARCH).rpm
ROOT			= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
MKD2PDF			?= $(shell which markdown-pdf)
VIRTUALENV		?= virtualenv
TEST			= tests
SPHINXBUILD		= sphinx-build
SPHINXSOURCEDIR	= docs
SPHINXBUILDDIR	= docs/build

ifeq ($(OS),Windows_NT)
	BIN = Scripts
	LIB = Lib
	TGZ_EXT = zip
	PYTHON ?= $(shell which python).exe
	PYTHON_EXE ?= $(shell where python | head -n1)
else
	BIN = bin
	LIB = lib/python2.7
	TGZ_EXT = tar.gz
	PYTHON ?= $(shell which python2.7)
	PYTHON_EXE = python2.7
endif

TMP=$(ROOT)/tmp
VENV_PREFIX = $(TMP)/.venv
VENV = $(VENV_PREFIX)/$(APP)
REQ = requirements.txt

TESTREQ = requirements_dev.txt

COVERAGE_ARGS=--with-coverage --cover-erase --cover-package=$(APP) \
               --cover-branches --cover-xml \
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
# @echo "    rpm           - Create $(PACKAGE) rpm"
	@echo "    egg           - Create python egg"
	@echo "    unittest      - Execute unit tests"
	@echo "    doc           - Build sphinx documentation"
	@echo "    coverage      - Execute unittests and code coverage"
	@echo

init:
	mkdir -p $(ROOT)/dist
	# mkdir -p $(TMP)/rpmbuild/SOURCES
	# mkdir -p $(TMP)/rpmbuild/BUILD
	# mkdir -p $(TMP)/rpmbuild/RPMS

sdist: init venv
	@echo ">>> Creating source distribution..."
	$(VENV)/$(BIN)/python setup.py sdist
	@echo ">>> OK. TGZ generated in $(ROOT)/dist"
	@echo

disabled-rpm: init sdist
	@echo ">>> Creating RPM package..."
	cp $(ROOT)/dist/$(APP)-$(VERSION).${TGZ_EXT} $(TMP)/rpmbuild/SOURCES
	rpmbuild -bb $(APP).spec                                                 \
             --define "version $(VERSION)"                                   \
             --define "release $(RELEASE)"                                   \
             --define "arch $(ARCH)"                                         \
             --define "_target_os linux"                                     \
             --define "_topdir $(TMP)/rpmbuild"                              \
             --define "buildroot $(TMP)/rpmbuild/BUILDROOT"                  \
             --define "__python $(PYTHON)"                                   \
             --define "python_sitelib $(VENV)/$(LIB)/site-packages"      \
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
	$@/$(BIN)/pip install --upgrade -r $(REQ); \
	$@/$(BIN)/pip install --upgrade -r $(TESTREQ); \

unittest: init venv
	$(VENV)/$(BIN)/pytest toolium/test

coverage: init venv
	$(VENV)/$(BIN)/nosetests $(COVERAGE_ARGS) $(UNIT_TEST_ARGS)
	@echo ">>> OK. Coverage reports generated in $(ROOT)/dist"

# Just for development purposes. It uses your active python2.7
# Remember to update your requirements if needed
egg:
	$(PYTHON_EXE) setup.py bdist_egg

# Just for development purposes. It uses your active python2.7
# Remember to update your requirements if needed
install:
	$(PYTHON_EXE) setup.py install

doc: venv
	@echo ">>> Cleaning sphinx doc files..."
	rm -rf $(SPHINXBUILDDIR)/html
	@echo ">>> Generating doc files..."
	$(VENV)/$(BIN)/$(SPHINXBUILD) -b html $(SPHINXSOURCEDIR) $(SPHINXBUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(SPHINXBUILDDIR)/html."

clean:
	@echo ">>> Cleaning temporal files..."
	rm -rf $(TMP) dist/ *.egg-info/ build/
	@echo

.PHONY: all clean venv install sdist egg unittest doc coverage