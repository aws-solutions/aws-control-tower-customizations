# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.7.3] - 2024-09-13
- Update dependencies
  - `PyYAML` 5.4.1 ([#154](https://github.com/aws-solutions/aws-control-tower-customizations/issues/154), [#169](https://github.com/aws-solutions/aws-control-tower-customizations/issues/169))
  - `Jinja2` 3.1.4 ([#169](https://github.com/aws-solutions/aws-control-tower-customizations/issues/169))
  - `requests` 2.32.2

## [2.7.2] - 2024-07-18
- Add support for AWS Regions: Asia Pacific (Hyderabad, Jakarta, and Osaka), Israel (Tel Aviv), Middle East (UAE), 
  and AWS GovCloud (US-East). Customers with these Regions as their AWS Control Tower home Region can now deploy 
  account customizations using the CfCT framework.
- Enable lifecycle configuration, enable access logging and add versioning on S3 buckets 
- Enhance security and robustness through improved handling of file paths and highly compressed data 
- Upgrade botocore to version 1.31.17 and boto3 to version 1.28.17

## [2.7.1] - 2024-05-30
* Update dependencies & runtimes ([#186]((https://github.com/aws-solutions/aws-control-tower-customizations/issues/186)), [#193]((https://github.com/aws-solutions/aws-control-tower-customizations/issues/193)))
  * Building the solution from source now requires Python 3.11 or higher
  * Update Python Lambda runtimes to 3.11
  * Update Ruby version to 3.3
  * Update CodeBuild container image to `aws/codebuild/standard:7.0`
* Pinned version for `PyYAML`  to 5.3.1 due to [yaml/pyyaml#724](https://github.com/yaml/pyyaml/issues/724) ([#183](https://github.com/aws-solutions/aws-control-tower-customizations/issues/183), [#184](https://github.com/aws-solutions/aws-control-tower-customizations/issues/184))
* Pinned version for `moto` to 4.2.14.
* Add `UpdateReplacePolicy` and `DeletionPolicy` to lifecycle event queue and DLQ to improve deployment safety.

## [2.7.0] - 2023-11-10
- Resolve `ConcurrentModificationException` errors that occur during parallel SCP deployments due to a race condition when enabling SCPs [#175](https://github.com/aws-solutions/aws-control-tower-customizations/issues/175)
- Improve performance when querying for StackSet instance account IDs in large organizations [#174](https://github.com/aws-solutions/aws-control-tower-customizations/issues/174)
- The CFCT pipeline now triggers on `UpdateManagedAccount` Control Tower lifecycle events, in addition to `CreateManagedAccount` events [#173](https://github.com/aws-solutions/aws-control-tower-customizations/issues/173)
- Honor the `CodeCommitBranchName` stack parameter on the CFCT repo’s initial commit. The example code is now committed to your chosen branch instead of `main` [#117](https://github.com/aws-solutions/aws-control-tower-customizations/issues/117)
- Enable the use of privately registered CloudFormation resources in customization templates (for example, the `AWSUtility::CloudFormation::CommandRunner` resource type) [#76](https://github.com/aws-solutions/aws-control-tower-customizations/issues/76)
- CFCT now ignores non-existent OU targets when deploying SCPs, aligning with how non-existent OUs are treated when deploying StackSets [#126](https://github.com/aws-solutions/aws-control-tower-customizations/issues/126)

## [2.6.0] - 2023-05-18
- Now supported in the following regions: me-south-1, af-south-1, eu-south-1, ap-east-1, us-west-1.
- Manifest now allows the use of S3 global urls to download template files and uses regional urls as a fallback mechanism.
- Eventbased triggers for CodePipeline deployments now supported.

## [2.5.3] - 2023-04-25
- Bugfix: Add S3 bucket policy necessary for new CfCT deployments

## [2.5.2] - 2022-12-12
- Fix bug where adding a resource to the middle of the manifest file caused CFCT to submit step function executions for all remaining manifest resources even if those resources had no changes
- Drop polling wait time for step function execution status from 30s to 15s

## [2.5.1] - 2022-10-19
- Add support for AWS GovCloud
- Please note: using CFCT in AWS GovCloud requires the Control Tower home region to be AWS GovCloud West (us-gov-west-1)

## [2.5.0] - 2022-08-26
- Support for opt-in deletion of Stack Set resources. This functionality is only supported when using the manifest v2 schema. Opting in to the new functionality reduces the overhead of manually deleting resources provisioned by CfCT.
  - In the manifest v2 schema, the `enable_stack_set_deletion` flag is set to `false` by default. In this configuration, when a resource is removed from Customizations for Control Tower's manifest, no actions will be taken against the StackSet removed.
  - Once opting into `enable_stack_set_deletion` by setting its value to `true` in the manifest, Removing a resource in its entirety from the manifest will delete the StackSet and all owned resources.
  - https://docs.aws.amazon.com/controltower/latest/userguide/cfct-delete-stack.html
>**Note:** With `enable_stack_set_deletion` set to `true`, on the next invocation of CfCT, **ALL** resources not declared in the manifest, that start with the prefix `CustomControlTower-` and have the associated Tag: `"Key": "AWS_Solutions", "Value": "CustomControlTowerStackSet"` will be deleted
- Bug Fix: Resolves a bug with CFCT versions >= 2.0.0 where using a v1 manifest format and defining a resource block without a parameter_file attribute (which is optional in v1 manifests) causes the CFCT pipeline to fail.

## [2.4.0] - 2022-06-08
- Add support for CfCT pipeline to fail if any stack instances within a stack set deployment have failed
  - New template parameter `EnforceSuccessfulStackInstances` can be set to True to achieve this behaviour
  - Previously, when customers set high fault tolerance values to get concurrent stack instance deployments, the CfCT pipeline would succeed even when stack instances failed, which caused cascading failures for customer workflow dependencies
- Bug-Fix: Add non-interactive flag to dpkg-reconfigure to support non-US-ACSII characters in template [#121](https://github.com/aws-solutions/aws-control-tower-customizations/issues/121)

## [2.3.1] - 2022-05-18
- Reduce CodeBuild runtime by removing unnecessary apt-get upgrade and apt-mark hold commands
- Update CodeBuild container image to aws/codebuild/standard:5.0. This should reduce CodeBuild queued and provisioning stage wait times.
- Fix bug related to Service Control Policy (SCP) deployment in organizations with >100 SCPs

## [2.3.0] - 2022-04-20
- Pinned version for MarkupSafe dependency to 2.0.1 due to https://github.com/pallets/jinja/issues/1585
- Pinned version of Amazon Corretto to java-1.8.0-amazon-corretto-jdk due to https://github.com/aws-solutions/aws-control-tower-customizations/issues/102
- Moved python code into its own package
- Building the solution from source now requires Python 3.6 or higher
- Customers should now download the [Customizations for AWS Control Tower CloudFormation Template](https://github.com/aws-solutions/aws-control-tower-customizations/blob/main/customizations-for-aws-control-tower.template) from GitHub instead of S3

## [2.2.0] - 2021-12-09
### Added 
- Added support for organization Root as an OU for manifest schema version "2021-03-15". [#8](https://github.com/aws-solutions/aws-control-tower-customizations/pull/8)
- Added support for nested OU for manifest schema version "2021-03-15". [#19](https://github.com/aws-solutions/aws-control-tower-customizations/issues/19)
- Added support for CAPABILITY_AUTO_EXPAND for SAM. [#78](https://github.com/aws-solutions/aws-control-tower-customizations/pull/78)
### Changed
- Fixed the issue that SSM parameter names were not output to logs for troubleshooting. [#68](https://github.com/aws-solutions/aws-control-tower-customizations/pull/68)
- Fixed the issue that resources starting with "S3" were incorrectly parsed as empty buckets. [#65](https://github.com/aws-solutions/aws-control-tower-customizations/issues/65)
- Fixed the issue that customization example folder was missing from the github repository. [#71](https://github.com/aws-solutions/aws-control-tower-customizations/issues/71)

## [2.1.0] - 2021-05-15
### Added
- Added option to enable concurrency to deploy StackSets operations in regions in parallel.
- Added support for UTF-8 encoded CloudFormation templates. [#55](https://github.com/aws-solutions/aws-control-tower-customizations/issues/55)
### Changed
- Support list of SSM Parameter Store keys as CloudFormation parameter value. [#43](https://github.com/aws-solutions/aws-control-tower-customizations/issues/43)
- Use environment variable for Update StackSet API [#50](https://github.com/aws-solutions/aws-control-tower-customizations/pull/50/files)
- Handle account names with overlapping string [#45](https://github.com/aws-solutions/aws-control-tower-customizations/issues/45)
- Handle SCP policy tag name with whitespace.
- Update parsing logic to learn manifest version in the manifest.

## [2.0.0] - 2021-03-15
### Added
- Support for new simplified manifest schema (version "2021-03-15"). This does not impact existing customers using manifest version "2020-01-01".
### Changed
- Optimization to skip update Stack Set workflow when only new accounts are added to the Stack Set.
- Ability to create only Stack Sets if the account list is empty. This allows users to configure Stack Set resources with empty Organizational Units. Ref:[GitHub Issue 42](https://github.com/aws-solutions/aws-control-tower-customizations/issues/42)
- Pinned versions for all the third-party packages.
- Update cfn-nag package to v0.7.2 to utilize new rules. This may result in new failures and warning in the build stage. However, it would help you identify new issues.
- Update default branch name to 'main'.
- Add support for https path for the resource file in the manifest.

## [1.2.1] - 2020-10-01
### Changed
- Fix the issue related to incompatibility between latest version of BotoCore and AWS CLI. Ref: [Boto3 Issue #2596](https://github.com/boto/boto3/issues/2596)

## [1.2.0] - 2020-06-20
### Added
- Feature to select AWS CodePipeline source (AWS CodeCommit repository or Amazon S3 bucket).
- Feature to switch between the two CodePipeline sources.
- Feature to use an existing AWS CodeCommit repository.
### Changed
- Uses Virtual Hosted-Style URLs (path-style URLs will be deprecated in Sept 2020).
- Uses regional endpoint for S3 APIs.
- Increases the stack set operation fault tolerance from 0 to 10 percent to allow parallel stack instance deployments.
- Updates the AWS CodeBuild image to the latest available version (aws/codebuild/standard:4.0).
- Optimizes the CloudFormation resource stage to trigger step function execution only if there is difference between the configuration and deployed stack sets.
- Fixes the issue in the build stage of the CodePipeline by updating manifest version to match the manifest schema.
- Fixes the issue for comparing deployed stack set templates and parameters [#4](https://github.com/aws-solutions/aws-control-tower-customizations/issues/4)
- Fixes the issue for updating the variables in the files using Jinja [#17](https://github.com/aws-solutions/aws-control-tower-customizations/issues/17)

## [1.1.0] - 2020-02-25
### Known Issue Fix and Code Optimization
- Fixed Stack Instance Deletion Issue: In case there are existing stack instances but
none of those instances belongs to the accounts specified in the user manifest
file as the input for the StackSet state machine, the deletion of the existing
stack instances would fail. This issue is not applicable if at least one account
in the input account list has an existing stack instance.
- Code Optimization for Best Practice

## [1.0.0] - 2020-01-10
### Added
- Initial public release