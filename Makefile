APP				= toolium
VERSION			?= $(shell cat VERSION)
ROOT                       = $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
SPHINXBUILD		= sphinx-build
SPHINXSOURCEDIR	= docs
SPHINXBUILDDIR	= docs/build
TMP             = $(ROOT)/tmp
VENV_PREFIX     = $(TMP)/.venv
VENV            = $(VENV_PREFIX)/$(APP)
REQ             = requirements.txt
TESTREQ         = requirements_dev.txt

ifeq ($(OS),Windows_NT)
	BIN = Scripts
	TGZ_EXT = zip
else
	BIN = bin
	TGZ_EXT = tar.gz
endif

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
	@echo "    egg           - Create python egg"
	@echo "    unittest      - Execute unit tests"
	@echo "    doc           - Build sphinx documentation"
	@echo "    coverage      - Execute unittests and code coverage"
	@echo

init:
	mkdir -p $(ROOT)/dist

venv: $(VENV)

$(VENV): $(REQ) $(TESTREQ)
	mkdir -p $@; \
	export GIT_SSL_NO_VERIFY=true; \
	$(PYTHON_EXE) -m venv $@; \
	source $(VENV)/$(BIN)/activate; \
	python -m pip install --upgrade -r $(REQ); \
	python -m pip install --upgrade -r $(TESTREQ);

sdist: init venv
	@echo ">>> Creating source distribution..."
	source $(VENV)/$(BIN)/activate; \
	python setup.py sdist
	@echo ">>> OK. TGZ generated in $(ROOT)/dist"
	@echo

unittest: init venv
	source $(VENV)/$(BIN)/activate; \
	python -m pytest toolium/test

coverage: init venv
	source $(VENV)/$(BIN)/activate; \
	coverage run --source=toolium -m pytest toolium/test
	@echo ">>> OK. Coverage reports generated in $(ROOT)/dist"

# Just for development purposes
# Remember to update your requirements if needed
egg:
	python -m pip install setuptools; \
	python setup.py bdist_egg

# Just for development purposes
# Remember to update your requirements if needed
install:
	python -m pip install setuptools; \
	python setup.py install

doc: init venv
	@echo ">>> Cleaning sphinx doc files..."
	rm -rf $(SPHINXBUILDDIR)/html
	@echo ">>> Generating doc files..."
	source $(VENV)/$(BIN)/activate; \
	$(SPHINXBUILD) -b html $(SPHINXSOURCEDIR) $(SPHINXBUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(SPHINXBUILDDIR)/html."

clean:
	@echo ">>> Cleaning temporal files..."
	rm -rf $(TMP) dist/ *.egg-info/ build/
	@echo

.PHONY: all clean venv install sdist egg unittest doc coverage