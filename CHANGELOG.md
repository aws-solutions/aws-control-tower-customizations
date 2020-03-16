# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2020-01-10
### Added
- Initial public release

## [1.1.0] - 2020-02-25
### Known Issue Fix and Code Optimization
- Stack Instance Deletion Issue: In case there are existing stack instances but
none of those instances belongs to the accounts specified in the user manifest
file as the input for the StackSet state machine, the deletion of the existing
stack instances would fail. This issue is not applicable if at least one account
in the input account list has an exsiting stack instance.
- Code Optimization for Best Practice