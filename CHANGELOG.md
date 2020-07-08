# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2020-01-10
### Added
- Initial public release

## [1.1.0] - 2020-02-25
### Known Issue Fix and Code Optimization
- Fixed Stack Instance Deletion Issue: In case there are existing stack instances but
none of those instances belongs to the accounts specified in the user manifest
file as the input for the StackSet state machine, the deletion of the existing
stack instances would fail. This issue is not applicable if at least one account
in the input account list has an existing stack instance.
- Code Optimization for Best Practice

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
- Fixes the issue for comparing deployed stack set templates and parameters [#4](https://github.com/awslabs/aws-control-tower-customizations/issues/4)
- Fixes the issue for updating the variables in the files using Jinja [#17](https://github.com/awslabs/aws-control-tower-customizations/issues/17)