import inspect
import os

from slackchannel2pdf.channel_exporter import SlackChannelExporter


currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def main():
    exporter = SlackChannelExporter(slack_token="TEST", add_debug_info=True)
    exporter._workspace_info = {"team": "test", "user_id": "U92345678"}
    exporter._user_names["U92345678"] = "Erik Kalkoken"
    exporter._user_names["U82345678"] = "Mei Tsukaya"
    exporter._user_names["U72345678"] = "Mr. Y"

    exporter._channel_names = {"G1234567X": "render-complete"}

    exporter.run(["render-complete"], currentdir)


if __name__ == "__main__":
    main()
