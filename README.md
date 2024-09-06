## Customizations for AWS Control Tower Solution
The Customizations for AWS Control Tower solution combines AWS Control Tower and other highly-available, trusted AWS services to help customers more quickly set up a secure, multi-account AWS environment based on AWS best practices. Customers can easily add customizations to their AWS Control Tower landing zone using an AWS CloudFormation template and service control policies (SCPs). Customers can deploy their custom template and policies to both individual accounts and organizational units (OUs) within their organization. Customizations for AWS Control Tower integrates with AWS Control Tower lifecycle events to ensure that resource deployments stay in sync with the customer's landing zone. For example, when a new account is created using the AWS Control Tower account factory, the solution ensures that all resources attached to the account's OUs will be automatically deployed. Before deploying this solution, customers need to have an AWS Control Tower landing zone deployed in their account.

## Getting Started 
To get started with Customizations for AWS Control Tower, please review the [documentation](https://docs.aws.amazon.com/controltower/latest/userguide/customize-landing-zone.html)

The solution can be deployed using one of three sources, S3, CodeCommit and GitHub.

## Deploying with S3 as the Source

### Running unit tests for customization 
* Clone the repository, then make the desired code changes 
* Next, run unit tests to make sure added customization passes the tests 

```  
chmod +x ./deployment/run-unit-tests.sh
./deployment/run-unit-tests.sh
``` 

### Building the customized solution
* Building the solution from source requires Python 3.6 or higher
* Configure the solution name, version number, bucket name and (optional) opt-in region support of your target Amazon S3 distribution bucket 

``` 
export DIST_OUTPUT_BUCKET_PREFIX=my-bucket-prefix # Prefix for the S3 bucket where customized code will be stored 
export TEMPLATE_OUTPUT_BUCKET=my-bucket-name # Name for the S3 bucket where the template will be stored
export SOLUTION_NAME=my-solution-name # name of the solution (e.g. customizations-for-aws-control-tower)
export VERSION=my-version # version number for the customized code  (e.g. 2.1.0)
export ENABLE_OPT_IN_REGION_SUPPORT=true # Optional flag to build with opt-in region support
```

* Update pip version to latest
```
python3 -m pip install -U pip
```


* Now build the distributable
``` 
chmod +x ./deployment/build-s3-dist.sh
./deployment/build-s3-dist.sh $DIST_OUTPUT_BUCKET_PREFIX $TEMPLATE_OUTPUT_BUCKET $SOLUTION_NAME $VERSION $ENABLE_OPT_IN_REGION_SUPPORT
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

### Deploying the customized solution
* Get the link of the custom-control-tower-initiation.template loaded to your Amazon S3 bucket. 
* Deploy the Customizations for AWS Control Tower solution to your account by launching a new AWS CloudFormation stack using the link of the custom-control-tower-initiation.template.

## Deploying with CodeCommit as the Source

### Deploying the solution
* Download the `custom-control-tower-initiation.template` from the root of this repository.
* Create a new AWS CloudFormation stack, using the `custom-control-tower-initiation.template` above.
 * Under **AWS CodePipeline Source**
   * Select `GAWS CodeCommit`
 * Under **AWS CodeCommit Setup (Applicable if 'AWS CodeCommit' was selected as the CodePipeline Source)**
   * **Existing CodeCommit Repository?** if you already have a repository in AWS CodeCommit, prepared for deploying CfCT, then select `Yes`  and provide the following to parameters. Otherwise select `No` and one will be created for you.
   * **CodeCommit Repository Name** the repository name (defaults to `custom-control-tower-configuration`)
   * **CodeCommit Branch Name** the branch name (defaults to `main`)

## Deploying with GitHub as the Source

### Prepare a GitHub Repository
Create a repository within your GitHub account, the default name used in the template `custom-control-tower-configuration`.
**Consider making the target repository private**. 
You'll define you customizations in a yaml file called `manifest.yaml` in the root of this repo. 

The [CfCT customization guide](https://docs.aws.amazon.com/controltower/latest/userguide/cfct-customizations-dev-guide.html) provides detailed guidance on creating a `manifest.yaml` to configure your customizations.

### Creating the Code Connection
* [Developer Tools - Connections](https://console.aws.amazon.com/codesuite/settings/connections) instance for GitHub
* Select **Create connection**
  * Select `GitHub` as the **provider**
  * **Create GitHub App connection** in **Connection name** type `GitHub - CfCT`
  * Select **Connect to GitHub**
* Connect to GitHub
  * Select **Install a new app**
  * Select the GitHub User/Organization for your repository
* AWS Connector for GitHub
  * Under **Repository access**, select **Only select repositories** and select only the repository you created earlier.
  * Select **Save**
* Note the Code Connections ARN - you'll need it when deploying the CloudFormation stack.

### Deploying the CloudFormation Stack
* Download the `custom-control-tower-initiation.template` from the root of this repository.
* Create a new AWS CloudFormation stack, using the `custom-control-tower-initiation.template` above.
 * Under **AWS CodePipeline Source** 
   * Select `GitHub (via Code Connection)`
 * Under **GitHub Setup (Applicable if 'GitHub (via Code Connection)' was selected as the CodePipeline Source)**
   * **ARN of the Code Connection** provide the `Code Connection ARN`
   * **GitHub User or Organization** type the GitHub user/organization under which you created the repository
   * **GitHub Repository Name** the repository name (defaults to `custom-control-tower-configuration`)
   * **GitHub Branch Name** the branch name (defaults to `main`)
 
## Collection of operational metrics

This solution collects anonymous operational metrics to help AWS improve the quality and features of the solution. For more information, including how to disable this capability, please see the [documentation here](https://docs.aws.amazon.com/controltower/latest/userguide/cfct-metrics.html).

## License

See license [here](https://github.com/aws-solutions/aws-control-tower-customizations/blob/main/LICENSE.txt) 
