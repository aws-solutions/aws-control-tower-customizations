#!/usr/bin/env bash

# Check to see if input has been provided:
if [ -z "$1" ]; then
    echo "Please provide the base source bucket name, trademark approved solution name and version where the lambda code will eventually reside."
    echo "For example: ./install_stage_dependencies.sh <STAGE_NAME>"
    echo "For example: ./install_stage_dependencies.sh build | scp | stackset"
    exit 1
fi

stage_name_argument=$1
build_stage_name='build'
scp_stage_name='scp'
stackset_stage_name='stackset'

install_common_pip_packages () {
    # install pip packages
    which python && python --version
    which python3 && python3 --version
    which pip && pip --version
    pip install --upgrade pip==21.0.1
    pip install --upgrade setuptools
    pip install --upgrade virtualenv==20.4.2
    pip install --upgrade PyYAML==5.3.1
    pip install --upgrade yorm==1.6.2
    pip install --upgrade jinja2==2.11.3
    pip install --upgrade boto3==1.17.3
    pip install --upgrade awscli==1.19.3
    pip install --upgrade requests==2.25.1
}

build_dependencies () {
    # install linux packages
    apt-get install rsync -y

    # install pip packages
    install_common_pip_packages
    pip install --upgrade pykwalify==1.8.0
    pip install cfn_flip==1.2.3
    pip freeze

    # Install CFN Nag
    ruby -v
    gem -v
    gem install cfn-nag -v 0.7.2
}

scp_dependencies () {
    # install pip packages
    install_common_pip_packages
    pip freeze
}

stackset_dependencies () {
    # install pip packages
    install_common_pip_packages
    pip freeze
}

if [ $stage_name_argument == $build_stage_name ];
then
    echo "Installing Build Stage Dependencies."
    build_dependencies
elif [ $stage_name_argument == $scp_stage_name ];
then
    echo "Installing SCP Stage Dependencies."
    scp_dependencies
elif [ $stage_name_argument == $stackset_stage_name ];
then
    echo "Installing StackSet Stage Dependencies."
    stackset_dependencies
else
    echo "Could not install dependencies. Argument didn't match one of the allowed values.
    >> build | scp | stackset"
fi
