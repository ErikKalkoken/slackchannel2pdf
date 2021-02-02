import argparse
import os
import sys

from dateutil import parser
import pytz
from babel import Locale, UnknownLocaleError

from . import __version__
from . import settings
from .channel_exporter import SlackChannelExporter


def main():
    """Implements the arg parser and starts the slackchannel2pdf with its input"""

    print(f"slackchannel2pdf v{__version__} by Erik Kalkoken")
    print("")

    args = parse_args(sys.argv[1:])
    start_export = True

    if "version" in args:
        print(__version__)
        start_export = False

    # try to take slack token from optional argument or environment variable
    if args.token is None:
        if "SLACK_TOKEN" in os.environ:
            slack_token = os.environ["SLACK_TOKEN"]
        else:
            print("ERROR: No slack token provided")
            start_export = False
            slack_token = None
    else:
        slack_token = args.token

    # parse local timezone
    if args.timezone is not None:
        try:
            my_tz = pytz.timezone(args.timezone)
        except pytz.UnknownTimeZoneError:
            print("ERROR: Unknown timezone")
            my_tz = None
            start_export = False
    else:
        my_tz = None

    # parse locale
    if args.locale is not None:
        try:
            my_locale = Locale.parse(args.locale, sep="-")
        except UnknownLocaleError:
            print("ERROR: provided locale string is not valid")
            start_export = False
            my_locale = None
    else:
        my_locale = None

    # parse oldest
    if args.oldest is not None:
        try:
            oldest = parser.parse(args.oldest)
        except ValueError:
            print("Invalid date input for --oldest")
            start_export = False
            oldest = None
    else:
        oldest = None

    # parse latest
    if args.latest is not None:
        try:
            latest = parser.parse(args.latest)
        except ValueError:
            print("Invalid date input for --latest")
            start_export = False
            latest = None
    else:
        latest = None

    if start_export:
        exporter = SlackChannelExporter(
            slack_token=slack_token,
            my_tz=my_tz,
            my_locale=my_locale,
            add_debug_info=args.add_debug_info,
        )
        exporter.run(
            channel_inputs=args.channel,
            dest_path=args.destination,
            oldest=oldest,
            latest=latest,
            page_orientation=args.page_orientation,
            page_format=args.page_format,
            max_messages=args.max_messages,
            write_raw_data=(args.write_raw_data is True),
        )


def parse_args(args) -> argparse.ArgumentParser:
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

    return my_arg_parser.parse_args(args)


if __name__ == "__main__":
    main()
