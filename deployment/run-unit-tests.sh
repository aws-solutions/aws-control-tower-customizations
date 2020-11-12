#!/bin/bash
echo 'pip3 install -r source/requirements.txt -t source/'
pip3 install -r source/requirements.txt -t source/
echo 'pip3 install -r source/testing_requirements.txt'
pip3 install -r source/testing_requirements.txt
echo 'cd source && pytest tests && cd -'
cd source && pytest tests && cd -
