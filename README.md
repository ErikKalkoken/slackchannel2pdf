# slackchannel2pdf

**slackchannel2pdf** is a command line tool for exporting the text contents of any Slack channel to a PDF file.

[![release](https://img.shields.io/pypi/v/slackchannel2pdf?label=release)](https://pypi.org/project/slackchannel2pdf/) [![python](https://img.shields.io/pypi/pyversions/slackchannel2pdf)](https://pypi.org/project/slackchannel2pdf/) [![licence](https://img.shields.io/github/license/ErikKalkoken/slackchannel2pdf)](https://github.com/ErikKalkoken/slackchannel2pdf/blob/master/LICENSE) [![pipeline](https://api.travis-ci.org/ErikKalkoken/slackchannel2pdf.svg?branch=master)](https://travis-ci.com/github/ErikKalkoken/slackchannel2pdf) [![codecov](https://codecov.io/gh/ErikKalkoken/slackchannel2pdf/branch/master/graph/badge.svg?token=omhTxW8ALq)](https://codecov.io/gh/ErikKalkoken/slackchannel2pdf) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Token](#token)
- [Usage](#usage)
- [Arguments](#arguments)
- [Limitations](#limitations)

## Overview

This tool is aimed at end users that want to make backups of Slack conversations or be able to share them outside Slack. It will create a PDF file for every exported channel and will work both for public and private channels.

**slackchannel2pdf** is an open source project and offered free of charge and under the MIT license. Please check attached licence file for details.

## Features

Here is a short summary of the key features of **slackchannel2pdf**:

- Export of any public and private Slack channel to a PDF file (text only)
- Automatic detection of timezone and locale based from Slack. Can also be set manually if needed.
- Exporting support for all Slack features incl. threads and layout blocks
- Ability to export only the portion of a channel for a specific time period
- Ability to configure page layout of PDF file (e.g. Portrait vs. Landscape)

## Installation

### Python

You can install the tool from PyPI with `pip install`. This wil require you to have Python reinstalled in your machine and it will work with any OS supported by Python. We recommend installing it into a virtual environment like venv.

```bash
pip install slackchannel2pdf
```

You can then run the tool with the command `slackchannel2pdf` as explained in detail under [Usage](#usage).

### Windows

For windows users we also provide a Windows EXE that does not require you to install Python. You find the EXE file under [releases](https://github.com/ErikKalkoken/slackchannel2pdf/releases).

## Token

To run **slackchannel2pdf** your need to have a token for your Slack workspace with the following permissions:

- `channels:history`
- `channels:read`
- `groups:history`
- `groups:read`
- `users:read`
- `usergroups:read`

## Usage

In order to use **slackchannel2pdf** you need:

1. have it installed on your system (see [Installation](#installation))
2. have a Slack token for the respective Slack workspace with the required permissions (see [Token](#token)).

Here are some examples on how to use **slackchannel2pdf**:

To export the Slack channel "general":

```bash
slackchannel2pdf --token MY_TOKEN general
```

To export the Slack channels "general", "random" and "test":

```bash
slackchannel2pdf --token MY_TOKEN general random test
```

To export all message from channel "general" starting from July 5th, 2019 at 11:00.

```bash
slackchannel2pdf --token MY_TOKEN --oldest "2019-JUL-05 11:00" general
```

> Tip: You can provide the Slack token either as command line argument `--token` or by setting the environment variable `SLACK-TOKEN`.

## Arguments

```text
usage: run.py [-h] [--token TOKEN] [--oldest OLDEST] [--latest LATEST]
              [-d DESTINATION] [--page-orientation {portrait,landscape}]
              [--page-format {a3,a4,a5,letter,legal}] [--timezone TIMEZONE]
              [--locale LOCALE] [--version] [--max-messages MAX_MESSAGES]
              [--write-raw-data] [--add-debug-info]
              channel [channel ...]

This program exports the text of a Slack channel to a PDF file

positional arguments:
  channel               One or several: name or ID of channel to export.

optional arguments:
  -h, --help            show this help message and exit
  --token TOKEN         Slack OAuth token (default: None)
  --oldest OLDEST       don't load messages older than a date (default: None)
  --latest LATEST       don't load messages newer then a date (default: None)
  -d DESTINATION, --destination DESTINATION
                        Specify a destination path to store the PDF file.
                        (TBD) (default: .)
  --page-orientation {portrait,landscape}
                        Orientation of PDF pages (default: portrait)
  --page-format {a3,a4,a5,letter,legal}
                        Format of PDF pages (default: a4)
  --timezone TIMEZONE   Manually set the timezone to be used e.g.
                        'Europe/Berlin' Use a timezone name as defined here: h
                        ttps://en.wikipedia.org/wiki/List_of_tz_database_time_
                        zones (default: None)
  --locale LOCALE       Manually set the locale to be used with a IETF
                        language tag, e.g. ' de-DE' for Germany. See this page
                        for a list of valid tags:
                        https://en.wikipedia.org/wiki/IETF_language_tag
                        (default: None)
  --version             show the program version and exit
  --max-messages MAX_MESSAGES
                        max number of messages to export (default: 10000)
  --write-raw-data      will also write all raw data returned from the API to
                        files, e.g. messages.json with all messages (default:
                        None)
  --add-debug-info      wether to add debug info to PDF (default: False)
```

## Limitations

- Text only: **slackchannel2pdf** will export only text from a channel, but not images or icons. This is by design.
- No Emojis: the tools is currently not able to write emojis as icons will will use their text representation instead (e.g. `:laughing:` instead of :laughing:).
- DMs, Group DM: Currently not supported
- Limited blocks support:Some non-text features of layout blocks not yet supported
- Limited script support: This tool is rendering all text with the [Google Noto Sans](https://www.google.com/get/noto/#sans-lgc) font and will therefore support all 500+ languages that are support by that font. It does however not support many Asian languages / scripts like Chinese, Japanese, Korean, Thai and others
