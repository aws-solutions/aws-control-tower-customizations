#!/bin/bash

ARTIFACT_BUCKET=$1
CURRENT_PATH=$(pwd)
SUCCESS=0
FAILED=1
EXIT_STATUS=$SUCCESS
VERSION_1='2020-01-01'
VERSION_2='2021-03-15'

set_failed_exit_status() {
  echo "^^^ Caught an error: Setting exit status flag to $FAILED ^^^"
  EXIT_STATUS=$FAILED
}

exit_shell_script() {
  echo "Exiting script with status: $EXIT_STATUS"
  if [[ $EXIT_STATUS == 0 ]]
    then
      echo "INFO: Validation test(s) completed."
      exit $SUCCESS
    else
      echo "ERROR: One or more validation test(s) failed."
      exit $FAILED
    fi
}

validate_template_file() {
  echo "Running aws cloudformation validate-template on $template_url"
  # TODO: Verify if this works if resource file is homed in opt-in region, and CT mgmt is homed in commercial region
  aws cloudformation validate-template --template-url "$template_url" --region "$AWS_REGION"
  if [ $? -ne 0 ]
  then
    echo "ERROR: CloudFormation template failed validation - $template_url"
    set_failed_exit_status
  fi

  echo "Print file encoding: $tmp_file "
  file -i "$tmp_file"
  echo "Running cfn_nag_scan on $tmp_file"
  cfn_nag_scan --input-path "$tmp_file"
  if [ $? -ne 0 ]
  then
    echo "ERROR: CFN Nag failed validation - $file_name"
    set_failed_exit_status
  fi
}

validate_parameter_file() {
  echo "Running json validation on $tmp_file"
  python -m json.tool < "$tmp_file"
  if [ $? -ne 0 ]
  then
    echo "ERROR: CloudFormation parameter file failed validation - $file_name"
    set_failed_exit_status
  else
    echo "NO ISSUE WITH JSON"
  fi
}

echo "Printing artifact bucket name: $ARTIFACT_BUCKET"

python3 -c 'import yaml,sys;yaml.safe_load(sys.stdin)' < manifest.yaml
if [ $? -ne 0 ]
then
  echo "ERROR: Manifest file is not valid YAML"
  set_failed_exit_status
fi

echo "Manifest file is a valid YAML"

# Validate manifest schema
MANIFEST_VERSION=$(/usr/bin/yq eval '.version' manifest.yaml)
echo "Found current manifest version: $MANIFEST_VERSION"
if [[ "$MANIFEST_VERSION" == "$VERSION_1" ]]
then
  echo "WARNING: You are using older version $VERSION_1 of the schema. We recommend you to update your manifest file schema. See Developer Guide for details."
  pykwalify -d manifest.yaml -s cfct/validation/manifest.schema.yaml -e cfct/validation/custom_validation.py
  if [ $? -ne 0 ]
  then
  echo "ERROR: Manifest file failed V1 schema validation"
  set_failed_exit_status
  fi
elif [[ "$MANIFEST_VERSION" == "$VERSION_2" ]]
then
  echo "Validating manifest with schema version: $VERSION_2"
  pykwalify -d manifest.yaml -s cfct/validation/manifest-v2.schema.yaml -e cfct/validation/custom_validation.py
  if [ $? -ne 0 ]
  then
  echo "ERROR: Manifest file failed V2 schema validation"
  set_failed_exit_status
  fi
else
  echo "ERROR: Invalid manifest schema version."
  set_failed_exit_status
fi

echo "Manifest file validated against the schema successfully"

# check each file in the manifest to make sure it exists
check_files=$(grep '_file:' < manifest.yaml | grep -v '^ *#' | tr -s ' ' | tr -d '\r' | cut -d ' ' -f 3)
for file_name in $check_files ; do
  # run aws cloudformation validate-template, cfn_nag_scan and json validate on all **remote** templates / parameters files
  if [[ $file_name == s3* ]]; then
    echo "S3 URL path found: $file_name"
    tmp_file=$(mktemp)
    echo "Downloading $file_name to $tmp_file"
    aws s3 cp "$file_name" "$tmp_file" --only-show-errors
    if [[ $? == 0 ]]; then
        echo "S3 URL exists: $file_name"
        if [[ $file_name == *template ]]; then
          # Reformat the S3 URL from s3://bucket/key to https://bucket.s3.amazonaws.com/key
          IFS='/' read -ra TOKENS <<< "$file_name"
          BUCKET=${TOKENS[2]}
          KEY=""
          for i in "${!TOKENS[@]}"; do
              if [[ i -gt 2 ]]; then
                  KEY="$KEY/${TOKENS[$i]}"
              fi
          done
          template_url="https://$BUCKET.s3.amazonaws.com/${KEY:1}"
          validate_template_file
        elif [[ $file_name == *json ]]; then
          validate_parameter_file
        fi
    else
      echo "ERROR: S3 URL does not exist: $file_name"
      set_failed_exit_status
    fi
  # check if the resource file path is starting with http
  elif [[ $file_name == http* ]]; then
    echo "HTTPS URL path exists: $file_name"
    tmp_file=$(mktemp)
    echo "Downloading $file_name"
    curl --fail -o "$tmp_file" "$file_name"
    if [[ $? == 0 ]]; then
        echo "HTTPS URL exists: $file_name"
        if [[ $file_name == *template ]]; then
          template_url=$file_name
          validate_template_file
        elif [[ $file_name == *json ]]; then
          validate_parameter_file
        fi
    else
      echo "ERROR: HTTPS URL does not exist: $file_name"
      set_failed_exit_status
  fi
  elif [ -f "$CURRENT_PATH"/"$file_name" ]; then
    echo "File $file_name exists"
  else
    echo "ERROR: File $file_name does not exist"
    set_failed_exit_status
  fi
done

# run aws cloudformation validate-template and cfn_nag_scan on all **local** templates
cd templates
TEMPLATES_DIR=$(pwd)
export TEMPLATES_DIR
echo "Changing path to template directory: $TEMPLATES_DIR/"
for template_name in $(find . -type f | grep -E '.template$|.yaml$|.yml$|.json$' | sed 's/^.\///') ; do
    echo "Uploading template: $template_name  to s3"
    aws s3 cp "$TEMPLATES_DIR"/"$template_name" s3://"$ARTIFACT_BUCKET"/validate/templates/"$template_name"
    if [ $? -ne 0 ]
    then
      echo "ERROR: Uploading template: $template_name to S3 failed"
      set_failed_exit_status
    fi
done

#V110556787: Intermittent CodeBuild stage failure due to S3 error: Access Denied
sleep_time=30
echo "Sleeping for $sleep_time seconds"
sleep $sleep_time

for template_name in $(find . -type f | grep -E '.template$|.yaml$|.yml$|.json$' | sed 's/^.\///') ; do
    echo "Running aws cloudformation validate-template on $template_name"
    aws cloudformation validate-template --template-url https://s3."$AWS_REGION".amazonaws.com/"$ARTIFACT_BUCKET"/validate/templates/"$template_name" --region "$AWS_REGION"
    if [ $? -ne 0 ]
    then
      echo "ERROR: CloudFormation template failed validation - $template_name"
      set_failed_exit_status
    fi
    # delete objects in bucket
    aws s3 rm s3://"$ARTIFACT_BUCKET"/validate/templates/"$template_name"
    echo "Print file encoding: $template_name"
    file -i "$TEMPLATES_DIR"/"$template_name"
    echo "Running cfn_nag_scan on $template_name"
    cfn_nag_scan --input-path "$TEMPLATES_DIR"/"$template_name"
    if [ $? -ne 0 ]
    then
      echo "ERROR: CFN Nag failed validation - $template_name"
      set_failed_exit_status
    fi
done

# run json validation on all the **local** parameter files

cd ../parameters
echo "Changing path to parameters directory: $(pwd)"
for parameter_file_name in $(find . -type f | grep '.json' | grep -v '.j2' | sed 's/^.\///') ; do
    echo "Running json validation on $parameter_file_name"
    python -m json.tool < "$parameter_file_name"
    if [ $? -ne 0 ]
    then
      echo "ERROR: CloudFormation parameter file failed validation - $parameter_file_name"
      set_failed_exit_status
    fi
done
cd ..

# calling return_code function
exit_shell_script