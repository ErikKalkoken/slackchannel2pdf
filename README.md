# channelexport

Export the text contents of any Slack channel to a PDF file

## About this tool

**channelexport** is a command line tool for exporting the text contents of any Slack channel to a PDF file.

It is written in Python 3 and can run an any platform that support Python.

## Usage

To use channelexport you need to have it installed on your system (see chapter Installation) and you need a Slack token for the respective Slack workspace with the required permissions (see chapter Token).

>>>
Note that you provide the Slack token both as command line argument or by setting the environment variable `SLACK-TOKEN`.
<<<

Here are some examples on how to use channelexport:

To export the Slack channel "general" with the provided token:

`channelexport --token MY_TOKEN general`

To export the Slack channels "general", "random" and "test" with the provided token:

`channelexport --token MY_TOKEN general random test`

## Arguments

```text
usage: run.py [-h] [--token TOKEN] [-d DESTINATION]
              [--page-orientation {portrait,landscape}]
              [--page-format {a3,a4,a5,letter,legal}] [--timezone TIMEZONE]
              [--timesystem {12,24}] [--version] [--max-messages MAX_MESSAGES]
              [--write-raw-data] [--add-debug-info]
              channel [channel ...]

positional arguments:
  channel               One or several: name or ID of channel to export.

optional arguments:
  -h, --help            show this help message and exit
  --token TOKEN         Slack Oauth token (default: None)
  -d DESTINATION, --destination DESTINATION
                        Specify a destination path to store the PDF file.
                        (TBD) (default: .)
  --page-orientation {portrait,landscape}
                        Orientation of PDF pages (default: portrait)
  --page-format {a3,a4,a5,letter,legal}
                        Format of PDF pages (default: a4)
  --timezone TIMEZONE   timezone name as defined here: https://en.wikipedia.or
                        g/wiki/List_of_tz_database_time_zones (default: UTC)
  --timesystem {12,24}  Set the time system used for output (default: 24)
  --version             show the program version and exit
  --max-messages MAX_MESSAGES
                        max number of messages to export (default: None)
  --write-raw-data      will also write all raw data returned from the API to
                        files, e.g. messages.json with all messages (default:
                        None)
  --add-debug-info      wether to add debug info to PDF (default: False)
```

## Installation

tbd.

## Token

You run channelexport you need to have a token for your Slack workspace with the following permissions:

Minimum:

- `channels:history`
- `channels:read`
- `users:read`
- `users:read`
- `usergroups:read`

Additional scopes for reading private channels and DMs:

- `groups:history`
- `groups:read`
- `im:history`
- `im:read`

## Known limitations

- Text only: channelexport will export only text from a channel, but not images or icons. This is by design
- No Emojis: the tools is currently not able to write emojis as icons will will use their text representation instead (e.g. `:laughing:` instead of :laughing:).
- Group DM: Currently not supported
