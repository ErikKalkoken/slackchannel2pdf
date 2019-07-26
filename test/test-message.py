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
        "user_id": "U0HBXN3H8"
    }
    exporter._user_names["U0HBXN3H8"] = "Erik Kalkoken"
    exporter._channel_names = {
        "TEST-MESSAGE": "test-message"
    }
    exporter.set_time_system(ChannelExporter._TIME_SYSTEM_12HRS)
    exporter.run(["test-message"])

if __name__ == '__main__':
    main()