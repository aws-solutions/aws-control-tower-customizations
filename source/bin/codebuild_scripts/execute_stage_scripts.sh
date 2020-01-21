#!/usr/bin/env bash

# Check to see if input has been provided:
if [ -z "$1" ]; then
    echo "Please provide the base source bucket name, trademark approved solution name and version where the lambda code will eventually reside."
    echo "For example: ./execute_stage_scripts.sh <STAGE_NAME>"
    echo "For example: ./execute_stage_scripts.sh build | scp | stackset"
    exit 1
fi

stage_name_argument=$1
log_level=$2
wait_time=$3
sm_arn=$4
artifact_bucket=$5
execution_mode=$6
bool_values=$7
none_type_values=$8
build_stage_name='build'
scp_stage_name='scp'
stackset_stage_name='stackset'
current=`pwd`
export current
manifest_file_path=$current/manifest.yaml


build_scripts () {
    echo 'Date: `date` Path: `pwd`'
    echo 'bash merge_directories.sh $none_type_values $bool_values'
    bash merge_directories.sh $none_type_values $bool_values
    echo 'Executing validation tests'
    echo 'bash $current/validation/run-validation.sh $artifact_bucket'
    bash $current/validation/run-validation.sh $artifact_bucket
    echo 'Installing validation tests completed `date`'
    echo 'Printing Merge Report'
    cat merge_report.txt
}

scp_scripts () {
    echo 'Date: `date` Path: `pwd`'
    echo 'python trigger_scp_sm.py $log_level $wait_time $manifest_file_path $sm_arn_scp $artifact_bucket'
    python trigger_scp_sm.py $log_level $wait_time $manifest_file_path $sm_arn $artifact_bucket
}

stackset_scripts () {
    echo 'Date: `date` Path: `pwd`'
    echo 'python trigger_stackset_sm.py $log_level $wait_time $manifest_file_path $sm_arn_scp $artifact_bucket $execution_mode'
    python trigger_stackset_sm.py $log_level $wait_time $manifest_file_path $sm_arn $artifact_bucket $execution_mode
}

if [ $stage_name_argument == $build_stage_name ];
then
    echo "Executing Build Stage Scripts."
    build_scripts
elif [ $stage_name_argument == $scp_stage_name ];
then
    echo "Executing SCP Stage Scripts."
    scp_scripts
elif [ $stage_name_argument == $stackset_stage_name ];
then
    echo "Executing StackSet Stage Scripts."
    stackset_scripts
else
    echo "Could not execute scripts. Argument didn't match one of the allowed values.
    >> build | scp | stackset"
fi
