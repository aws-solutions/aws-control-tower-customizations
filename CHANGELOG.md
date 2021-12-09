# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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