import inspect
import os

from slackchannel2pdf.slackchannel2pdf import SlackChannelExporter


currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe()))
)


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
    exporter.run(["render-minimal"], currentdir)


if __name__ == '__main__':
    main()
