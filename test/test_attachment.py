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
    exporter._user_names["UBBKA171Q"] = "Mr. X"
    exporter._user_names["U9PTYC16J"] = "Mr. Y"
    exporter._channel_names = {
        "test_attachment": "test-attachments"
    }
    exporter.run("test_attachment")

if __name__ == '__main__':
    main()