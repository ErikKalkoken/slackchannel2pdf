import os
from channel_exporter import ChannelExporter

def main():
    exporter = ChannelExporter(os.environ['SLACK_TOKEN'])
    exporter.run("G2VKYMXEH", 100)    

if __name__ == '__main__':
    main()
