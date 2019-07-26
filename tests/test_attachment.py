import unittest
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir + "/channelexport")
from channelexport import ChannelExporter

def main():
    exporter = ChannelExporter("TEST")
    exporter._workspace_info = {
        "team": "Dummy",
        "user_id": "U92345678"
    }
    exporter._user_names["U92345678"] = "Erik Kalkoken"
    exporter._user_names["U82345678"] = "Mr. X"
    exporter._user_names["U72345678"] = "Mr. Y"
    exporter._channel_names = {
        "TEST-ATTACHMENT": "test_attachment"
    }
    exporter.run(["test_attachment"])

if __name__ == '__main__':
    main()