# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2020-01-10
### Added
- Initial public release

### Known Issues
- Single Value Change Issue: In case there is only a single value in the account list or region list in the 
StackSet state machine input, the replacement of the old single value with a new single
value does not successfully delete the stack instance in the old account or region. 
This issue is not applicable if there is more than one value in either account or region
list.