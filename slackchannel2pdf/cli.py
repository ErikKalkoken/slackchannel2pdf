"""command line interface"""

import argparse
import os
import sys
from pathlib import Path

import pytz
from babel import Locale, UnknownLocaleError
from dateutil import parser
from slack_sdk.errors import SlackApiError

from . import __version__, settings
from .channel_exporter import SlackChannelExporter


def main():
    """Implements the arg parser and starts the channel exporter with its input"""

    args = parse_args(sys.argv[1:])
    if "version" in args:
        print(__version__)
        exit(0)

    # try to take slack token from optional argument or environment variable
    if args.token is None:
        if "SLACK_TOKEN" in os.environ:
            slack_token = os.environ["SLACK_TOKEN"]
        else:
            print("ERROR: No slack token provided")
            exit(1)
    else:
        slack_token = args.token

    # parse local timezone
    if args.timezone is not None:
        try:
            my_tz = pytz.timezone(args.timezone)
        except pytz.UnknownTimeZoneError:
            print("ERROR: Unknown timezone")
            exit(1)
    else:
        my_tz = None

    # parse locale
    if args.locale is not None:
        try:
            my_locale = Locale.parse(args.locale, sep="-")
        except UnknownLocaleError:
            print("ERROR: provided locale string is not valid")
            exit(1)
    else:
        my_locale = None

    # parse oldest
    if args.oldest is not None:
        try:
            oldest = parser.parse(args.oldest)
        except ValueError:
            print("ERROR: Invalid date input for --oldest")
            exit(1)
    else:
        oldest = None

    # parse latest
    if args.latest is not None:
        try:
            latest = parser.parse(args.latest)
        except ValueError:
            print("ERROR: Invalid date input for --latest")
            exit(1)
    else:
        latest = None

    if not args.quiet:
        channel_postfix = "s" if args.channel and len(args.channel) > 1 else ""
        print(f"Exporting channel{channel_postfix} from Slack...")
    try:
        exporter = SlackChannelExporter(
            slack_token=slack_token,
            my_tz=my_tz,
            my_locale=my_locale,
            add_debug_info=args.add_debug_info,
        )
    except SlackApiError as ex:
        print(f"ERROR: {ex}")
        exit(1)

    result = exporter.run(
        channel_inputs=args.channel,
        dest_path=Path(args.destination) if args.destination else None,
        oldest=oldest,
        latest=latest,
        page_orientation=args.page_orientation,
        page_format=args.page_format,
        max_messages=args.max_messages,
        write_raw_data=(args.write_raw_data is True),
    )
    for channel in result["channels"].values():
        if not args.quiet:
            print(
                f"{'written' if channel['ok'] else 'failed'}: {channel['filename_pdf']}"
            )


def parse_args(args: list) -> argparse.ArgumentParser:
    """defines the argument parser and returns parsed result from given argument"""
    my_arg_parser = argparse.ArgumentParser(
        description="This program exports the text of a Slack channel to a PDF file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # main arguments
    my_arg_parser.add_argument(
        "channel", help="One or several: name or ID of channel to export.", nargs="+"
    )
    my_arg_parser.add_argument("--token", help="Slack OAuth token")
    my_arg_parser.add_argument("--oldest", help="don't load messages older than a date")
    my_arg_parser.add_argument("--latest", help="don't load messages newer then a date")

    # PDF file
    my_arg_parser.add_argument(
        "-d",
        "--destination",
        help="Specify a destination path to store the PDF file. (TBD)",
        default=".",
    )

    # formatting
    my_arg_parser.add_argument(
        "--page-orientation",
        help="Orientation of PDF pages",
        choices=["portrait", "landscape"],
        default=settings.PAGE_ORIENTATION_DEFAULT,
    )
    my_arg_parser.add_argument(
        "--page-format",
        help="Format of PDF pages",
        choices=["a3", "a4", "a5", "letter", "legal"],
        default=settings.PAGE_FORMAT_DEFAULT,
    )
    my_arg_parser.add_argument(
        "--timezone",
        help=(
            "Manually set the timezone to be used e.g. 'Europe/Berlin' "
            "Use a timezone name as defined here: "
            "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
        ),
    )
    my_arg_parser.add_argument(
        "--locale",
        help=(
            "Manually set the locale to be used with a IETF language tag, "
            "e.g. ' de-DE' for Germany. "
            "See this page for a list of valid tags: "
            "https://en.wikipedia.org/wiki/IETF_language_tag"
        ),
    )

    # standards
    my_arg_parser.add_argument(
        "--version",
        help="show the program version and exit",
        action="version",
        version=__version__,
    )

    # exporter config
    my_arg_parser.add_argument(
        "--max-messages",
        help="max number of messages to export",
        type=int,
        default=settings.MAX_MESSAGES_PER_CHANNEL,
    )

    # Developer needs
    my_arg_parser.add_argument(
        "--write-raw-data",
        help=(
            "will also write all raw data returned from the API to files,"
            " e.g. messages.json with all messages"
        ),
        action="store_const",
        const=True,
    )
    my_arg_parser.add_argument(
        "--add-debug-info",
        help="wether to add debug info to PDF",
        action="store_const",
        const=True,
        default=False,
    )
    my_arg_parser.add_argument(
        "--quiet",
        action="store_const",
        const=True,
        default=False,
        help=(
            "When provided will not generate normal console output, "
            "but still show errors "
            "(console logging not affected and needs to be configured through "
            "log levels instead)"
        ),
    )
    return my_arg_parser.parse_args(args)


if __name__ == "__main__":
    main()
