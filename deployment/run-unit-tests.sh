#!/bin/bash
# This script must be executed from the package root directory

set -e

if [ ! -d "testing-venv" ]; then
    echo "Creating testing-venv..."
    python3 -m venv testing-venv
fi


echo "Rebuilding package locally before testing..."
source testing-venv/bin/activate
echo "Using python: `type python3`"
echo "Python version: `python3 --version`"
echo "Installing pip"
pip3 install --quiet -U pip
echo "Installing CFCT library"
pip3 install --quiet "./source/src[test, dev]"
echo "Running tests..."
python3 -m pytest -m unit

deactivate