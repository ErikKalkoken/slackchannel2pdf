import unittest
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir + "/channelexport")
from channelexport import SlackChannelExporter

def main():
    exporter = SlackChannelExporter("TEST")
    exporter._workspace_info = {
        "team": "test",
        "user_id": "U92345678"
    }
    exporter._user_names["U92345678"] = "Erik Kalkoken"
    exporter._channel_names = {
        "G12345678": "render-minimal"
    }
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    exporter.run(["render-minimal"], currentdir)

if __name__ == '__main__':
    main()