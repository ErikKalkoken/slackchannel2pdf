# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - yyyy-mm-dd

## [1.2.2] - 2021-02-03

### Fixed

- 'NoneType' object has no attribute 'get_display_name'

## [1.2.1] - 2021-02-03

### Fixed

- Missing timestamp for posts in thread [#5](https://github.com/ErikKalkoken/slackchannel2pdf/issues/5)

## [1.2.0] - 2021-02-02

### Changed

- Major refactoring
- Now also uses paging to fetch list of users

### Fixed

- Works with general and random but not other channels [#4](https://github.com/ErikKalkoken/slackchannel2pdf/issues/4)

## [1.1.4] - 2020-12-07

### Changed

- Improved test coverage

### Fixed

- Error 'pretty type' - cant' export slack channel to pdf [#3](https://github.com/ErikKalkoken/slackchannel2pdf/issues/3)

## [1.1.3] - 2020-11-27

### Changed

- Now using Black for code styling

### Fixed

- Can not create PDF file on windows if team name contains characters not valid for file names, i.e. `<>:"/\|?*`

## [1.1.2] - 2020-04-01

### Fixed

- Installation from PyPI does not work probably

## [1.1.1] - 2020-04-01

### Added

- Technical improvements (flake8 compliance)

## [1.1.0] - 2020-04-01

### Added

- You can now run the tool from shell after pip install
- Added description of installation options

## [1.0.0] - 2019-08-05

### Added

- Initial release
