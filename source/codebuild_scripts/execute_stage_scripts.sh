#!/usr/bin/env bash

# Check to see if input has been provided:
if [ -z "$1" ]; then
    echo "Please provide the base source bucket name, trademark approved solution name and version where the lambda code will eventually reside."
    echo "For example: ./execute_stage_scripts.sh <STAGE_NAME>"
    echo "For example: ./execute_stage_scripts.sh build | scp | rcp | stackset"
    exit 1
fi

STAGE_NAME_ARGUMENT=$1
LOG_LEVEL=$2
WAIT_TIME=$3
SM_ARN=$4
ARTIFACT_BUCKET=$5
KMS_KEY_ALIAS_NAME=$6
BOOL_VALUES=$7
NONE_TYPE_VALUES=$8
BUILD_STAGE_NAME="build"
SCP_STAGE_NAME="scp"
RCP_STAGE_NAME="rcp"
STACKSET_STAGE_NAME="stackset"
CURRENT=$(pwd)
MANIFEST_FILE_PATH=$CURRENT/manifest.yaml

build_scripts () {
    echo "Date: $(date) Path: $(pwd)"
    echo "bash merge_directories.sh $NONE_TYPE_VALUES $BOOL_VALUES"
    bash merge_directories.sh "$NONE_TYPE_VALUES" "$BOOL_VALUES"
    echo "Executing validation tests"
    echo "bash run-validation.sh $ARTIFACT_BUCKET"
    bash run-validation.sh "$ARTIFACT_BUCKET"
    if [ $? == 0 ]
    then
      echo "Exit code: $? returned from the validation script."
      echo "INFO: Validation test(s) completed."
    else
      echo "Exit code: $? returned from the validation script."
      echo "ERROR: One or more validation test(s) failed."
      exit 1
    fi
    echo "Printing Merge Report"
    cat merge_report.txt
}

scp_scripts () {
    echo "Date: $(date) Path: $(pwd)"
    echo "python state_machine_trigger.py $LOG_LEVEL $WAIT_TIME $MANIFEST_FILE_PATH $SM_ARN $ARTIFACT_BUCKET $SCP_STAGE_NAME $KMS_KEY_ALIAS_NAME"
    python state_machine_trigger.py "$LOG_LEVEL" "$WAIT_TIME" "$MANIFEST_FILE_PATH" "$SM_ARN" "$ARTIFACT_BUCKET" "$SCP_STAGE_NAME" "$KMS_KEY_ALIAS_NAME"
}

rcp_scripts () {
    echo "Date: $(date) Path: $(pwd)"
    echo "python state_machine_trigger.py $LOG_LEVEL $WAIT_TIME $MANIFEST_FILE_PATH $SM_ARN $ARTIFACT_BUCKET $RCP_STAGE_NAME $KMS_KEY_ALIAS_NAME"
    python state_machine_trigger.py "$LOG_LEVEL" "$WAIT_TIME" "$MANIFEST_FILE_PATH" "$SM_ARN" "$ARTIFACT_BUCKET" "$RCP_STAGE_NAME" "$KMS_KEY_ALIAS_NAME"
}

stackset_scripts () {
    echo "Date: $(date) Path: $(pwd)"
    echo "python state_machine_trigger.py $LOG_LEVEL $WAIT_TIME $MANIFEST_FILE_PATH $SM_ARN $ARTIFACT_BUCKET $STACKSET_STAGE_NAME $KMS_KEY_ALIAS_NAME"
    python state_machine_trigger.py "$LOG_LEVEL" "$WAIT_TIME" "$MANIFEST_FILE_PATH" "$SM_ARN" "$ARTIFACT_BUCKET" "$STACKSET_STAGE_NAME" "$KMS_KEY_ALIAS_NAME" "$ENFORCE_SUCCESSFUL_STACK_INSTANCES"
}

if [ "$STAGE_NAME_ARGUMENT" == $BUILD_STAGE_NAME ];
then
    echo "Executing Build Stage Scripts."
    build_scripts
elif [ "$STAGE_NAME_ARGUMENT" == $SCP_STAGE_NAME ];
then
    echo "Executing SCP Stage Scripts."
    scp_scripts
elif [ "$STAGE_NAME_ARGUMENT" == $RCP_STAGE_NAME ];
then
    echo "Executing RCP Stage Scripts."
    rcp_scripts    
elif [ "$STAGE_NAME_ARGUMENT" == $STACKSET_STAGE_NAME ];
then
    echo "Executing StackSet Stage Scripts."
    stackset_scripts
else
    echo "Could not execute scripts. Argument didn't match one of the allowed values.
    >> build | scp | stackset"
fi
