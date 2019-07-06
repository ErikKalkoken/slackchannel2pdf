from channel_exporter import ChannelExporter
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(
        description='Tool for exporting Slack channels to PDF'
        )
    parser.add_argument(
        "-t", 
        "--token", 
        dest="token", 
        help="Slack Oauth token", 
        required=True
        )
    parser.add_argument(
        "-c", 
        "--channel", 
        dest="channel", 
        help="ID of channel to export", 
        required=True
        )
    parser.add_argument(
        "-m", 
        "--max-messages", 
        dest="max_messages", 
        help="max number of messages to export"
        )
    parser.add_argument(
        "-D", 
        "--debug", 
        dest="debug_mode", 
        help="run in debug mode",
        choices=['true', 'false'],
        default='false'
        )
    args = parser.parse_args()
    
    exporter = ChannelExporter(args.token)
    exporter.run(args.channel, args.max_messages, args.debug_mode=='true')

if __name__ == '__main__':
    main()
