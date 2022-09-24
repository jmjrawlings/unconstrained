#!/usr/bin/env bash

# Recompile project requirements
cd requirements
pip-compile requirements-prod.in -o requirements-prod.txt
pip-compile requirements-test.in -o requirements-test.txt
pip-compile requirements-dev.in -o requirements-dev.txt
pip-sync requirements-dev.txt