import unittest
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
from channel_exporter import ChannelExporter

def main():
    exporter = ChannelExporter("TEST")
    exporter._workspace_info = {
        "team": "Dummy",
        "user_id": "U0HBXN3H8"
    }
    exporter._user_names["U0HBXN3H8"] = "Erik Kalkoken"
    exporter._user_names["U0UGVN9GF"] = "Mei Tsukaya"
    exporter._channel_names = {
        "test_thread": "test-thread"
    }
    exporter.run("test_thread")

if __name__ == '__main__':
    main()