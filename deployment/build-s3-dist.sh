#!/bin/bash
# This assumes all of the OS-level configuration has been completed and git repo has already been cloned         
#
# Usage: This script should be executed from the package root directory
# ./deployment/build-s3-dist.sh source-bucket-base-name template-bucket-base-name trademarked-solution-name version-code enable-opt-in-region-support
#
# Parameters:                                                                                                   
# - source-bucket-base-name: Name for the S3 bucket location where the template will source the Lambda          
#    code from. The template will append '-[region_name]' to this bucket name.                                   
#    For example: ./build-s3-dist.sh solutions template-bucket my-solution v1.0.0                                              
#    The template will then expect the source code to be located in the solutions-[region_name] bucket           
#  
# - template-bucket-base-name: Name for the S3 bucket location where the template will be located                                                                                                           
#  
# - trademarked-solution-name: name of the solution for consistency                                             
#                                                                                                                
# - version-code: version of the package
#
# - enable-opt-in-region-support: (Optional Boolean) Flag to enable opt-in region support. Pass `true` to set this argument.


# Hard exit on failure
set -e

# Check to see if input has been provided:                                                                       
if [ $# -lt 4 ]; then
    echo "Please provide the base source bucket name, template-bucket, trademark approved solution name, version and (Optional) enable-opt-in-region-support flag"
    echo "For example: ./deployment/build-s3-dist.sh solutions template-bucket trademarked-solution-name v1.0.0 true"
    exit 1
fi

# declare variables
template_dir="$PWD"
template_dist_dir="$template_dir/deployment/global-s3-assets"
build_dist_dir="$template_dir/deployment/regional-s3-assets"
CODE_BUCKET_NAME=$1
TEMPLATE_BUCKET_NAME=$2
SOLUTION_NAME=$3
VERSION_NUMBER=$4
ENABLE_OPT_IN_REGION_SUPPORT=$5

# Handle opt-in region builds in backwards compatible way,
# Requires customer to set IS_OPT_IN_REGION parameter 
SCRIPT_BUCKET_NAME=$(echo "${TEMPLATE_BUCKET_NAME}")
DISTRIBUTION_BUCKET_NAME=$(echo "${TEMPLATE_BUCKET_NAME}")
if [[ "${ENABLE_OPT_IN_REGION_SUPPORT}" = "true" ]]; then
  echo "Building with opt-in region support"
  SCRIPT_BUCKET_NAME+='-${AWS_REGION}' # Regionalized Buildspec
  DISTRIBUTION_BUCKET_NAME+='-${AWS::Region}' # Regionalized CFN Template
fi

 echo "------------------------------------------------------------------------------"
 echo "[Init] Clean old dist and recreate directories"
 echo "------------------------------------------------------------------------------"
 echo "rm -rf $template_dist_dir"
 rm -rf "$template_dist_dir"
 echo "mkdir -p $template_dist_dir"
 mkdir -p "$template_dist_dir"
 echo "rm -rf $build_dist_dir"
 rm -rf "$build_dist_dir"
 echo "mkdir -p $build_dist_dir"
 mkdir -p "$build_dist_dir"

# Upgrade setuptools, wheel
# Install cython<3.0.0 and pyyaml 5.4.1 with build isolation
# Ref: https://github.com/yaml/pyyaml/issues/724
pip3 install --upgrade setuptools wheel
pip3 install 'cython<3.0.0' && pip3 install --no-build-isolation pyyaml==5.4.1

# Create zip file for AWS Lambda functions
echo -e "\n Creating all lambda functions for Custom Control Tower Solution"
python3 deployment/lambda_build.py state_machine_lambda deployment_lambda build_scripts lifecycle_event_handler state_machine_trigger

# Move custom-control-tower-initiation.template to global-s3-assets
echo "cp -f deployment/custom-control-tower-initiation.template $template_dist_dir"
cp -f deployment/custom-control-tower-initiation.template "$template_dist_dir"

#COPY deployment/add-on to $build_dist_dir/add-on
mkdir "$template_dist_dir"/add-on/
cp -f -R deployment/add-on/. "$template_dist_dir"/add-on

#COPY custom_control_tower_configuration to global-s3-assets
#Please check to see if this is the correct location or template_dist_dir
cp -f -R deployment/custom_control_tower_configuration "$build_dist_dir"/custom_control_tower_configuration/

echo -e "\n Updating code source bucket in the template with $CODE_BUCKET_NAME"
replace="s/%DIST_BUCKET_NAME%/$CODE_BUCKET_NAME/g"
echo "sed -i -e $replace $template_dist_dir/custom-control-tower-initiation.template"
sed -i -e "$replace" "$template_dist_dir"/custom-control-tower-initiation.template

echo -e "\n Updating template bucket in the template with $DISTRIBUTION_BUCKET_NAME"
replace="s/%TEMPLATE_BUCKET_NAME%/$DISTRIBUTION_BUCKET_NAME/g"
echo "sed -i -e $replace $template_dist_dir/custom-control-tower-initiation.template"
sed -i -e "$replace" "$template_dist_dir"/custom-control-tower-initiation.template

echo -e "\n Updating template bucket in the template with $SCRIPT_BUCKET_NAME"
replace="s/%SCRIPT_BUCKET_NAME%/$SCRIPT_BUCKET_NAME/g"
echo "sed -i -e $replace $template_dist_dir/custom-control-tower-initiation.template"
sed -i -e "$replace" "$template_dist_dir"/custom-control-tower-initiation.template

# Replace solution name with real value
echo -e "\n Updating solution name in the template with $SOLUTION_NAME"
replace="s/%SOLUTION_NAME%/$SOLUTION_NAME/g"
echo "sed -i -e $replace $template_dist_dir/custom-control-tower-initiation.template"
sed -i -e "$replace" "$template_dist_dir"/custom-control-tower-initiation.template

echo -e "\n Updating version number in the template with $VERSION_NUMBER"
replace="s/%VERSION%/$VERSION_NUMBER/g"
echo "sed -i -e $replace $template_dist_dir/custom-control-tower-initiation.template"
sed -i -e "$replace" "$template_dist_dir"/custom-control-tower-initiation.template

# Create configuration zip file
echo -e "\n Creating zip file with Custom Control Tower configuration"
cd "$build_dist_dir"/custom_control_tower_configuration/
zip -Xr "$build_dist_dir"/custom-control-tower-configuration.zip ./*

# build regional config zip file
echo -e "\n*** Build regional config zip file"
# Support all regions in https://docs.aws.amazon.com/controltower/latest/userguide/region-how.html + GovCloud regions
declare -a region_list=(
    "af-south-1"
    "ap-east-1"
    "ap-northeast-1"
    "ap-northeast-2"
    "ap-northeast-3"
    "ap-south-1"
    "ap-southeast-1"
    "ap-southeast-2"
    "ap-southeast-3"
    "ca-central-1"
    "eu-central-1"
    "eu-north-1"
    "eu-south-1"
    "eu-west-1"
    "eu-west-2"
    "eu-west-3"
    "me-south-1"
    "sa-east-1"
    "us-east-1"
    "us-east-2"
    "us-gov-east-1"
    "us-gov-west-1"
    "us-west-1"
    "us-west-2"
    "il-central-1"
    "me-central-1"
    "ap-south-2"
    "ap-southeast-3"
)
for region in "${region_list[@]}"
do
  echo -e "\n Building config zip for $region region"
  echo -e " Updating region name in the manifest to: $region \n"
  replace="s/{{ region }}/$region/g"
  cp ./manifest.yaml.j2 ./manifest.yaml
  echo "sed -i -e $replace ./manifest.yaml"
  sed -i -e "$replace" ./manifest.yaml
  echo -e "\n Zipping configuration..."
  zip -Xr "$build_dist_dir"/custom-control-tower-configuration-"$region".zip ./manifest.yaml ./example-configuration/*
done
cd -
#Copy Lambda Zip Files to the Global S3 Assets
echo -e "\n Copying lambda zip files to Global S3 Assets"
cp "$build_dist_dir"/*.zip "$template_dist_dir"/

