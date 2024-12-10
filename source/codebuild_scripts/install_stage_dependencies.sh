#!/usr/bin/env bash

# Check to see if input has been provided:
if [ -z "$1" ]; then
    echo "Please provide the base source bucket name, trademark approved solution name and version where the lambda code will eventually reside."
    echo "For example: ./install_stage_dependencies.sh <STAGE_NAME>"
    echo "For example: ./install_stage_dependencies.sh build | scp | rcp | stackset"
    exit 1
fi

stage_name_argument=$1
build_stage_name='build'
scp_stage_name='scp'
rcp_stage_name='rcp'
stackset_stage_name='stackset'

install_common_pip_packages () {
    # install pip packages
    pip install --quiet --upgrade pip==21.0.1
    pip install --quiet --upgrade setuptools
    pip install --quiet --upgrade wheel
    pip install --quiet --upgrade virtualenv==20.4.2
    pip install --quiet "cython<3.0.0" && pip install --quiet --no-build-isolation pyyaml==5.4.1
    pip install --quiet --upgrade yorm==1.6.2
    pip install --quiet --upgrade jinja2==2.11.3
    pip install --quiet --upgrade requests==2.25.1
}

build_dependencies () {
    # install linux packages
    apt-get -q install rsync -y 1> /dev/null
    VERSION=v4.8.0
    BINARY=yq_linux_amd64
    wget --quiet https://github.com/mikefarah/yq/releases/download/${VERSION}/${BINARY} -O /usr/bin/yq && chmod +x /usr/bin/yq

    # install pip packages
    install_common_pip_packages
    pip install --quiet --upgrade pykwalify==1.8.0
    pip install --quiet cfn_flip==1.2.3

    # Install CFN Nag
    gem install --quiet cfn-nag -v 0.7.2
}

scp_dependencies () {
    # install pip packages
    install_common_pip_packages
}

rcp_dependencies () {
    # install pip packages
    install_common_pip_packages
}

stackset_dependencies () {
    # install pip packages
    install_common_pip_packages
}

if [ $stage_name_argument == $build_stage_name ];
then
    echo "Installing Build Stage Dependencies."
    build_dependencies
elif [ $stage_name_argument == $scp_stage_name ];
then
    echo "Installing SCP Stage Dependencies."
    scp_dependencies
elif [ $stage_name_argument == $rcp_stage_name ];
then
    echo "Installing RCP Stage Dependencies."
    rcp_dependencies    
elif [ $stage_name_argument == $stackset_stage_name ];
then
    echo "Installing StackSet Stage Dependencies."
    stackset_dependencies
else
    echo "Could not install dependencies. Argument didn't match one of the allowed values.
    >> build | scp | stackset"
fi
