#!/bin/bash
# $1 is the $ARTIFACT_BUCKET from CodePipeline
python3 -c 'import yaml,sys;yaml.safe_load(sys.stdin)' < manifest.yaml
if [ $? -ne 0 ]
then
  echo "Manifest file is not valid YAML"
  exit 1
fi

echo "Manifest file is a valid YAML"

# Validate manifest schema
pykwalify -d manifest.yaml -s validation/manifest.schema.yaml -e validation/custom_validation.py
if [ $? -ne 0 ]
then
  echo "Manifest file failed schema validation"
  exit 1
fi

echo "Manifest file validated against the schema successfully"

# check each file in the manifest to make sure it exists
export current=`pwd`
check_files=$(grep '_file:' < manifest.yaml | grep -v '^ *#' | tr -s ' ' | tr -d '\r' | cut -d ' ' -f 3)
for f in $check_files ; do
  # run aws cloudformation validate-template, cfn_nag_scan and json validate on all **remote** templates / parameters files
  if [[ $f == s3* ]]; then
    echo "S3 URL exists: $f"
    tmp_file=$(mktemp)
    echo "Downloading $f to $tmp_file"
    aws s3 cp $f $tmp_file --only-show-errors
    if [[ $? == 0 ]]; then
        echo "S3 URL exists: $f"
        if [[ $f == *template ]]; then
          # Reformat the S3 URL from s3://bucket/key to https://bucket.s3.amazonaws.com/key
          IFS='/' read -ra TOKENS <<< "$f"
          BUCKET=${TOKENS[2]}
          KEY=""
          for i in "${!TOKENS[@]}"; do
              if [[ i -gt 2 ]]; then
                  KEY="$KEY/${TOKENS[$i]}"
              fi
          done
          template_url="https://$BUCKET.s3.amazonaws.com/${KEY:1}"

          echo "Running aws cloudformation validate-template on $template_url"
          aws cloudformation validate-template --template-url $template_url --region $AWS_REGION
          if [ $? -ne 0 ]
          then
            echo "CloudFormation template failed validation - $template_url"
            exit 1
          fi

          echo "Running cfn_nag_scan on $tmp_file"
          cfn_nag_scan --input-path $tmp_file
          if [ $? -ne 0 ]
          then
            echo "CFN Nag failed validation - $f"
            exit 1
          fi
        elif [[ $f == *json ]]; then
          echo "Running json validation on $tmp_file"
          python -m json.tool < $tmp_file
          if [ $? -ne 0 ]
          then
            echo "CloudFormation parameter file failed validation - $f"
            exit 1
          fi
        fi
    else
      echo "S3 URL does not exist: $f"
      exit 1
    fi
  elif [ -f $current'/'$f ]; then
    echo "File $f exists"
  else
    echo "File $f does not exist"
    exit 1
  fi
done

# run aws cloudformation validate-template and cfn_nag_scan on all **local** templates
cd templates
export deployment_dir=`pwd`
echo "$deployment_dir/"
for i in $(find . -type f | grep -E '.template$|.yaml$|.yml$|.json$' | sed 's/^.\///') ; do
    echo "Uploading template: $i  to s3"
    aws s3 cp $deployment_dir/$i s3://$1/validate/templates/$i
    if [ $? -ne 0 ]
    then
      echo "Uploading template: $i to S3 failed"
      exit 1
    fi
done

#V110556787: Intermittent CodeBuild stage failure due to S3 error: Access Denied
sleep_time=30
echo "Sleeping for $sleep_time seconds"
sleep $sleep_time

for i in $(find . -type f | grep -E '.template$|.yaml$|.yml$|.json$' | sed 's/^.\///') ; do
    echo "Running aws cloudformation validate-template on $i"
    aws cloudformation validate-template --template-url https://s3.$AWS_REGION.amazonaws.com/$1/validate/templates/$i --region $AWS_REGION
    if [ $? -ne 0 ]
    then
      echo "CloudFormation template failed validation - $i"
      exit 1
    fi
    # delete objects in bucket
    aws s3 rm s3://$1/validate/templates/$i
    echo "Running cfn_nag_scan on $i"
    cfn_nag_scan --input-path $deployment_dir/$i
    if [ $? -ne 0 ]
    then
      echo "CFN Nag failed validation - $i"
      exit 1
    fi
done

# run json validation on all the **local** parameter files

cd ../parameters
export deployment_dir=`pwd`
echo "$deployment_dir/"
for i in $(find . -type f | grep '.json' | grep -v '.j2' | sed 's/^.\///') ; do
    echo "Running json validation on $i"
    python -m json.tool < $i
    if [ $? -ne 0 ]
    then
      echo "CloudFormation parameter file failed validation - $i"
      exit 1
    fi
done
cd ..
