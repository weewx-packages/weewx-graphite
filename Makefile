# Makefile for WeeWX Graphite Extension.
#
# Source:: https://github.com/ampledata/weewx_graphite
# Author:: Greg Albrecht W2GMD <oss@undef.net>
# Copyright:: Copyright 2016 Orion Labs, Inc.
# License:: Apache License, Version 2.0
# Modified 2026-10-23 by weewx-packages: install with weectl.
#


.DEFAULT_GOAL := all
TARGETS=install.py bin/user/graphite.py


all: install

install:
	weectl extension install .


install_requirements:
	pip install -r requirements.txt

clean:
	@rm -rf *.egg* build dist *.py[oc] */*.py[co] cover doctest_pypi.cfg \
		nosetests.xml pylint.log output.xml flake8.log tests.log \
		test-result.xml htmlcov fab.log .coverage

pep8: install_requirements
	flake8 --max-complexity 12 --exit-zero $(TARGETS)

lint: install_requirements
	pylint --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" \
		-r n $(TARGETS) || exit 0

test: lint pep8
