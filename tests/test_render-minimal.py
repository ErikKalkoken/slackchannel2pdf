import unittest
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir + "/channelexport")
from channelexport import ChannelExporter

def main():
    exporter = ChannelExporter("TEST")
    exporter._workspace_info = {
        "team": "test",
        "user_id": "U92345678"
    }
    exporter._user_names["U92345678"] = "Erik Kalkoken"
    exporter._channel_names = {
        "G12345678": "render-minimal"
    }
    exporter.set_time_system(ChannelExporter._TIME_SYSTEM_12HRS)
    exporter.run(["render-minimal"], currentdir)

if __name__ == '__main__':
    main()