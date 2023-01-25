## Customizations for AWS Control Tower Solution
The Customizations for AWS Control Tower solution combines AWS Control Tower and other highly-available, trusted AWS services to help customers more quickly set up a secure, multi-account AWS environment based on AWS best practices. Customers can easily add customizations to their AWS Control Tower landing zone using an AWS CloudFormation template and service control policies (SCPs). Customers can deploy their custom template and policies to both individual accounts and organizational units (OUs) within their organization. Customizations for AWS Control Tower integrates with AWS Control Tower lifecycle events to ensure that resource deployments stay in sync with the customer's landing zone. For example, when a new account is created using the AWS Control Tower account factory, the solution ensures that all resources attached to the account's OUs will be automatically deployed. Before deploying this solution, customers need to have an AWS Control Tower landing zone deployed in their account.

## Getting Started 
To get started with Customizations for AWS Control Tower, please review the [documentation](https://docs.aws.amazon.com/controltower/latest/userguide/customize-landing-zone.html)

## Running unit tests for customization 
* Clone the repository, then make the desired code changes 
* Next, run unit tests to make sure added customization passes the tests 

```  
chmod +x ./deployment/run-unit-tests.sh
./deployment/run-unit-tests.sh
``` 

## Building the customized solution
* Building the solution from source requires Python 3.8 or higher
* Configure the solution name, version number and bucket name of your target Amazon S3 distribution bucket 

``` 
export DIST_OUTPUT_BUCKET_PREFIX=my-bucket-prefix # Prefix for the S3 bucket where customized code will be stored 
export TEMPLATE_OUTPUT_BUCKET=my-bucket-name # Name for the S3 bucket where the template will be stored
export SOLUTION_NAME=my-solution-name # name of the solution (e.g. customizations-for-aws-control-tower)
export VERSION=my-version # version number for the customized code  (e.g. 2.1.0)
```

* Update pip version to latest
```
python3 -m pip install -U pip
```


* Now build the distributable
``` 
chmod +x ./deployment/build-s3-dist.sh
./deployment/build-s3-dist.sh $DIST_OUTPUT_BUCKET_PREFIX $TEMPLATE_OUTPUT_BUCKET $SOLUTION_NAME $VERSION
``` 
 
* Upload the distributable to an Amazon S3 bucket in your account.

  * Upload the AWS CloudFormation template to your global bucket in the following pattern
    ``` 
    s3://my-bucket-name/$SOLUTION_NAME/$VERSION/ 
    ``` 

  * Upload the customized source code zip packages to your regional bucket in the following pattern
    ``` 
    s3://my-bucket-name-$REGION/$SOLUTION_NAME/$VERSION/
    ``` 

## Deploying the customized solution
* Get the link of the custom-control-tower-initiation.template loaded to your Amazon S3 bucket. 
* Deploy the Customizations for AWS Control Tower solution to your account by launching a new AWS CloudFormation stack using the link of the custom-control-tower-initiation.template.


## Collection of operational metrics

This solution collects anonymous operational metrics to help AWS improve the quality and features of the solution. For more information, including how to disable this capability, please see the [documentation here](https://docs.aws.amazon.com/controltower/latest/userguide/cfct-metrics.html).

## License

See license [here](https://github.com/aws-solutions/aws-control-tower-customizations/blob/main/LICENSE.txt) 
