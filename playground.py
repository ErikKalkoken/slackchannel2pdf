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
    args = parser.parse_args()
    print(args.token)
    print(args.channel)

if __name__ == '__main__':
    main()
