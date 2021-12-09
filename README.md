## Customizations for AWS Control Tower Solution
The Customizations for AWS Control Tower solution combines AWS Control Tower and other highly-available, trusted AWS services to help customers more quickly set up a secure, multi-account AWS environment based on AWS best practices. Customers can easily add customizations to their AWS Control Tower landing zone using an AWS CloudFormation template and service control policies (SCPs). Customers can deploy their custom template and policies to both individual accounts and organizational units (OUs) within their organization. Customizations for AWS Control Tower integrates with AWS Control Tower lifecycle events to ensure that resource deployments stay in sync with the customer's landing zone. For example, when a new account is created using the AWS Control Tower account factory, the solution ensures that all resources attached to the account's OUs will be automatically deployed. Before deploying this solution, customers need to have an AWS Control Tower landing zone deployed in their account.

## Getting Started 
To get started with the Customizations for AWS Control Tower solution, please review the [solution documentation](https://aws.amazon.com/solutions/implementations/customizations-for-aws-control-tower/)

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
export DIST_OUTPUT_BUCKET_PREFIX=my-source-code-bucket-name_prefix # Prefix for the S3 bucket where customized code will reside 
export TEMPLATE_OUTPUT_BUCKET=my-template-bucket-name # Name for the S3 bucket where the template will be located
export SOLUTION_NAME=customizations-for-aws-control-tower # name of the solution 
export VERSION=my-version # version number for the customized code  
export REGION=aws-region-code # the AWS region to test the solution (e.g. us-east-1)
``` 
_Note:_ You would need to create one global bucket and one regional bucket. The global bucket TEMPLATE_OUTPUT_BUCKET, for example "my-bucket-name", is used to store the AWS CloudFormation template. The regional bucket <DIST_OUTPUT_BUCKET_PREFIX>-<REGION>, for example "my-bucket-name-us-east-1", is used to store your customized source code zip packages (lambda code). The solution's CloudFormation template will expect the source code to be located in a bucket matching that name. Also, the assets in bucket should be publicly accessible.
 
* Now build the distributable
``` 
chmod +x ./build-s3-dist.sh
./build-s3-dist.sh $DIST_OUTPUT_BUCKET_PREFIX $TEMPLATE_OUTPUT_BUCKET $SOLUTION_NAME $VERSION
``` 
 
* Upload the distributable to an Amazon S3 bucket in your account.

  * Upload the AWS CloudFormation template to your global bucket in the following pattern
    ``` 
    s3://my-bucket-name/$SOLUTION_NAME/$VERSION/ 
    ``` 

  * Upload the customized source code zip packages to your regional bucket in the following pattern
    ``` 
    s3://my-bucket-name-<REGION>/$SOLUTION_NAME/$VERSION/
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

Below shows the file structure of a custom configuration package which can be found in the github source code. Note that this is an example, therefore file path, folder and file names can be modified by customers to match what is defined in the manifest file.

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

## Collection of operational metrics

This solution collects anonymous operational metrics to help AWS improve the quality and features of the solution. For more information, including how to disable this capability, please see the [implementation guide](https://docs.aws.amazon.com/solutions/latest/customizations-for-aws-control-tower/appendix-b.html).

## License

See license [here](https://github.com/aws-solutions/aws-control-tower-customizations/blob/main/LICENSE.txt) 