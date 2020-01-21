#!/bin/bash
# This assumes all of the OS-level configuration has been completed and git repo has already been cloned         
#                                                                                                                
# This script should be run from the repo's deployment directory                                                 
# cd deployment                                                                                                  
# ./build-s3-dist.sh source-bucket-base-name trademarked-solution-name version-code                              
#                                                                                                                
# Paramenters:                                                                                                   
#  - source-bucket-base-name: Name for the S3 bucket location where the template will source the Lambda          
#    code from. The template will append '-[region_name]' to this bucket name.                                   
#    For example: ./build-s3-dist.sh solutions my-solution v1.0.0                                                
#    The template will then expect the source code to be located in the solutions-[region_name] bucket           
#                                                                                                                
#  - trademarked-solution-name: name of the solution for consistency                                             
#                                                                                                                
#  - version-code: version of the package                                                                        

# Check to see if input has been provided:                                                                       
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Please provide the base source bucket name, trademark approved solution name and version where the lambda code will eventually reside."
    echo "For example: ./build-s3-dist.sh solutions trademarked-solution-name v1.0.0"
    exit 1
fi

# Get reference for all important folders
template_dir="$PWD"
template_dist_dir="$template_dir/deployment/global-s3-assets"
build_dist_dir="$template_dir/deployment/regional-s3-assets"

 echo "------------------------------------------------------------------------------"
 echo "[Init] Clean old dist and recreate directories"
 echo "------------------------------------------------------------------------------"
 echo "rm -rf $template_dist_dir"
 rm -rf $template_dist_dir
 echo "mkdir -p $template_dist_dir"
 mkdir -p $template_dist_dir
 echo "rm -rf $build_dist_dir"
 rm -rf $build_dist_dir
 echo "mkdir -p $build_dist_dir"
 mkdir -p $build_dist_dir

# Create zip file for AWS Lambda functions
echo -e "\n Creating all lambda functions for Custom Control Tower Solution"
python source/bin/build_scripts/lambda_build.py state_machine_lambda deployment_lambda build_scripts scp_state_machine_trigger stackset_state_machine_trigger lifecycle_event_handler

echo -e "\n Cleaning up the tests folder from the lambda zip files"
zip -d $build_dist_dir/custom-control-tower-config-deployer.zip tests/*
zip -d $build_dist_dir/custom-control-tower-state-machine.zip tests/*
zip -d $build_dist_dir/custom-control-tower-scripts.zip tests/*
zip -d $build_dist_dir/custom-control-tower-lifecycle-event-handler.zip tests/*

# Move custom-control-tower-initiation.template to global-s3-assets
echo "cp -f deployment/custom-control-tower-initiation.template $template_dist_dir"
cp -f deployment/custom-control-tower-initiation.template $template_dist_dir

#COPY deployment/add-on to $build_dist_dir/add-on
mkdir $template_dist_dir/add-on/
cp -f -R deployment/add-on/. $template_dist_dir/add-on

#COPY custom_control_tower_configuration to global-s3-assets
#Please check to see if this is the correct location or template_dist_dir
cp -f -R deployment/custom_control_tower_configuration $build_dist_dir/custom_control_tower_configuration/

echo -e "\n Updating code source bucket in the template with $1"
replace="s/%DIST_BUCKET_NAME%/$1/g"
echo "sed -i -e $replace $template_dist_dir/custom-control-tower-initiation.template"
sed -i -e $replace $template_dist_dir/custom-control-tower-initiation.template

cd $template_dist_dir/add-on
for y in `find . -name "*.template"`;
  do
    echo "sed -i -e $replace $y"
    sed -i -e $replace $y
  done
cd ../../..

echo -e "\n Updating template bucket in the template with $2"
replace="s/%TEMPLATE_BUCKET_NAME%/$2/g"
echo "sed -i -e $replace $template_dist_dir/custom-control-tower-initiation.template"
sed -i -e $replace $template_dist_dir/custom-control-tower-initiation.template
echo "sed -i -e $replace $build_dist_dir/$rss_file_name"
sed -i -e $replace $build_dist_dir/$rss_file_name

cd $template_dist_dir/add-on
for y in `find . -name "*.template"`;
  do
    echo "sed -i -e $replace $y"
    sed -i -e $replace $y
  done
cd ../../..

# Replace solution name with real value
echo -e "\n >> Updating solution name in the template with $3"
replace="s/%SOLUTION_NAME%/$3/g"
echo "sed -i -e $replace $template_dist_dir/custom-control-tower-initiation.template"
sed -i -e $replace $template_dist_dir/custom-control-tower-initiation.template

cd $template_dist_dir/add-on
for y in `find . -name "*.template"`;
  do
    echo "sed -i -e $replace $y"
    sed -i -e $replace $y
  done
cd ../../..

echo -e "\n Updating version number in the template with $4"
replace="s/%VERSION%/$4/g"
echo "sed -i -e $replace $template_dist_dir/custom-control-tower-initiation.template"
sed -i -e $replace $template_dist_dir/custom-control-tower-initiation.template

echo "sed -i -e $replace $template_dist_dir/$rss_file_name"
sed -i -e $replace $template_dist_dir/$rss_file_name

cd $template_dist_dir/add-on
for y in `find . -name "*.template"`;
  do
    echo "sed -i -e $replace $y"
    sed -i -e $replace $y
  done
cd ../../..

# Create configuration zip file
echo -e "\n Creating zip file with Custom Control Tower configuration"
cd $build_dist_dir/custom_control_tower_configuration/;  zip -Xr $build_dist_dir/custom-control-tower-configuration.zip ./* ; cd -

#Copy Lambda Zip Files to the Global S3 Assets
echo -e "\n Copying lambda zip files to Global S3 Assets"
cp $build_dist_dir/*.zip $template_dist_dir/

