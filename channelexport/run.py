# Copyright 2019 Erik Kalkoken
#
# Licensed under MIT license. See attached file for details
#
# This package contains the implementation of the command line interface
# for Channelexport
#

import os
import argparse
import pytz
from channelexport import ChannelExporter

def main():
    """Implements the arg parser and starts the channelexporter with its input"""

    # main arguments
    parser = argparse.ArgumentParser(
        description = "This program exports the text of a Slack channel to a PDF file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )    
    parser.add_argument(        
        "channel", 
        help = "One or several: name or ID of channel to export.",
        nargs="+"
        )
    
    parser.add_argument(
        "--token",         
        help = "Slack Oauth token"
        )

    # PDF file
    parser.add_argument(        
        "-d",
        "--destination",         
        help = "Specify a destination path to store the PDF file. (TBD)",
        default = "."
        )
    
    # formatting
    parser.add_argument(        
        "--page-orientation",         
        help = "Orientation of PDF pages",
        choices = ["portrait", "landscape"],
        default = ChannelExporter._PAGE_ORIENTATION_DEFAULT
        )
    parser.add_argument(        
        "--page-format",         
        help = "Format of PDF pages",
        choices = ["a3", "a4", "a5", "letter", "legal"],
        default = ChannelExporter._PAGE_FORMAT_DEFAULT
        )
    parser.add_argument(
        "--timezone",         
        help = "timezone name as defined here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
        default = ChannelExporter._TZ_DEFAULT
        )    

    parser.add_argument(        
        "--timesystem",         
        help = "Set the time system used for output",
        type=int,
        choices = ChannelExporter._TIME_SYSTEMS,
        default = ChannelExporter._TIME_SYSTEM_DEFAULT
        )

    # standards
    parser.add_argument(        
        "--version",         
        help="show the program version and exit", 
        action="version", 
        version=ChannelExporter._VERSION
        )    

    # exporter config
    parser.add_argument(        
        "--max-messages",         
        help = "max number of messages to export",
        type = int
        )

    # Developer needs
    parser.add_argument(        
        "--write-raw-data",
        help = "will also write all raw data returned from the API to files,"\
            + " e.g. messages.json with all messages",                
        action = "store_const",
        const = True
        )    
    
    parser.add_argument(        
        "--add-debug-info",
        help = "wether to add debug info to PDF",
        action = "store_const",
        const = True,
        default = False
        )

    start_export = True
    args = parser.parse_args()

    if args.timezone not in pytz.all_timezones:
        print("ERROR: Unknown timezone: " + args.timezone)
        start_export = False
    
    if "version" in args:
        print(ChannelExporter._VERSION)            
        start_export = False

    # try to take slack token from optional argument or environment variable
    if args.token is None:
        if "SLACK_TOKEN" in os.environ:
            slack_token = os.environ['SLACK_TOKEN']
        else:
            print("ERROR: No slack token provided")
            start_export = False
    else:
        slack_token = args.token

    if start_export:
        exporter = ChannelExporter(slack_token, args.add_debug_info)
        if "timezone" in args:
            exporter.tz_local_name = args.timezone
        if "timesystem" in args:
            exporter.set_time_system(args.timesystem)
        exporter.run(
            args.channel, 
            args.max_messages, 
            args.write_raw_data == True
        )
    

if __name__ == '__main__':
    main()