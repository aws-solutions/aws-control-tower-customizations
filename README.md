## Customizations for AWS Control Tower Solution
The Customizations for AWS Control Tower solution combines AWS Control Tower and other highly-available, trusted AWS services to help customers more quickly set up a secure, multi-account AWS environment based on AWS best practices. Customers can easily add customizations to their AWS Control Tower landing zone using an AWS CloudFormation template and service control policies (SCPs). Customers can deploy their custom template and policies to both individual accounts and organizational units (OUs) within their organization. Customizations for AWS Control Tower integrates with AWS Control Tower lifecycle events to ensure that resource deployments stay in sync with the customer's landing zone. For example, when a new account is created using the AWS Control Tower account factory, the solution ensures that all resources attached to the account's OUs will be automatically deployed.

## Getting Started 
To get started with the Customizations for AWS Control Tower solution, please review the solution documentation. https://aws.amazon.com/solutions/customizations-for-aws-control-tower

## Running unit tests for customization 
* Clone the repository, then make the desired code changes 
* Next, run unit tests to make sure added customization passes the tests 

``` 
chmod +x ./deployment/run-unit-tests.sh
./deployment/run-unit-tests.sh
``` 

## Building the customized solution
* Configure the solution name, version number and bucket name of your target Amazon S3 distribution bucket 
``` 
export SOLUTION_NAME=customizations-for-aws-control-tower # name of the solution
export DIST_OUTPUT_BUCKET=my-bucket-name # bucket where customized code will reside 
export VERSION=my-version # version number for the customized code 
``` 
_Note:_ You would have to create an S3 bucket with prefix 'my-bucket-name-<aws_region>'; aws_region is where you are testing the customized solution. Also, the assets in bucket should be publicly accessible 
 
* Now build the distributable: 
``` 
chmod +x ./build-s3-dist.sh
./build-s3-dist.sh $DIST_OUTPUT_BUCKET $SOLUTION_NAME $VERSION
``` 
 
* Deploy the distributable to an Amazon S3 bucket in your account. _Note:_ you must have the AWS Command Line Interface installed. 
``` 
aws s3 cp deployment/global-s3-assets/  s3://my-bucket-name-<aws_region>/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control --profile aws-cred-profile-name 
aws s3 cp deployment/regional-s3-assets/ s3://my-bucket-name-<aws_region>/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control --profile aws-cred-profile-name
``` 

## Deploying the customized solution
* Get the link of the custom-control-tower-initiation.template loaded to your Amazon S3 bucket. 
* Deploy the Customizations for AWS Control Tower solution to your account by launching a new AWS CloudFormation stack using the link of the custom-control-tower-initiation.template.

## File Structure
The  File structure of the Customizations for AWS Control Tower solution consists of a deployment directory that contains AWS CloudFormation template and build scripts, and a source directory that contains python source code.

```
customizations-for-aws-control-tower
├── deployment
│   ├── build-s3-dist.sh                            [ shell script for packaging distribution assets ]
│   ├── run-unit-tests.sh                           [ shell script for executing unit tests ]
│   ├── custom-control-tower-initiation.template    [ solution CloudFormation deployment template ]
│   └── custom_control_tower_configuration          [ custom configuration examples ]
│       └── example-configuration
└── source  
    ├── bin                                         
    │   ├── build_scripts                           [ python scripts for packaging the source code ]
    │   └── codebuild_scripts                       [ shell and python scripts for codebuild project ]
    ├── lib                                         [ dependencies used in the solution ]
    ├── tests                                       [ unit tests ]
    └── validation                                  [ shell and python scripts for validating manifest schema and cfn template]
```

Below shows the file structure of a custom configuration package. Note that this is an example, therefore file path, folder and file names can be modified by customers to match what is defined in the manifest file.

```
custom_control_tower_configuration
├── manifest.yaml                       [ custom configuration file. Required ]
├── parameters                        
│   ├── create-ssm-parameter-keys-1.json   [ json file one containing input parameters used in the template file, if any. Optional ]
│   └── create-ssm-parameter-keys-2.json   [ json file two containing input parameters used in the template file, if any. Optional ]
├── policies
│   └── preventive-guardrails.json             [ json file containing service control policies (preventive guardrails). required for SCPs ] 
└── templates
    ├── create-ssm-parameter-keys-1.template  [ CloudFormation template one for creating ssm parameter resources. required for StackSet ] 
    └── create-ssm-parameter-keys-2.template  [ CloudFormation template two for creating ssm parameter resources. required for StackSet ] 
```   
***

Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

http://www.apache.org/licenses/LICENSE-2.0  

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.