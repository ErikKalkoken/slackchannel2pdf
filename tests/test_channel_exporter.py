import inspect
import os
import unittest
from unittest.mock import patch

from datetime import datetime
import pytz
from tzlocal import get_localzone
import babel
import PyPDF2

from slackchannel2pdf import __version__
from slackchannel2pdf import settings
from slackchannel2pdf.channel_exporter import SlackChannelExporter

from .no_sockets import NoSocketsTestCase
from .testtools import SlackClientStub


currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


class TestExporterTransformText(NoSocketsTestCase):
    def setUp(self):
        workspace_info = {"team": "test", "user_id": "U9234567X"}
        user_names = {
            "U12345678": "Naoko Kobayashi",
            "U62345678": "Janet Hakuli",
            "U72345678": "Yuna Kobayashi",
            "U9234567X": "Erik Kalkoken",
            "U92345678": "Rosie Dunbar",
        }

        channel_names = {
            "C12345678": "berlin",
            "C72345678": "tokio",
            "C42345678": "oslo",
            "G1234567X": "channel-exporter",
            "G2234567X": "channel-exporter-2",
        }

        usergroup_names = {
            "S12345678": "admins",
            "S72345678": "marketing",
            "S42345678": "sales",
        }

        self.exporter = SlackChannelExporter("TEST")
        self.exporter._slack_service._workspace_info = workspace_info
        self.exporter._slack_service._user_names = user_names
        self.exporter._slack_service._channel_names = channel_names
        self.exporter._slack_service._usergroup_names = usergroup_names
        self.exporter._slack_service._author = "Erik Kalkoken"

    def test_run_with_defaults(self):
        channels = ["G1234567X", "G2234567X"]
        response = self.exporter.run(channels, currentdir)
        self.assertTrue(response["ok"])
        self.assertIn("G1234567X", response["channels"])
        self.assertIn("G2234567X", response["channels"])

        for channel_id in ["G1234567X", "G2234567X"]:
            res_channel = response["channels"][channel_id]
            channel_name = self.exporter._slack_service.channel_names()[channel_id]
            self.assertEqual(
                res_channel["filename_pdf"],
                os.path.join(
                    currentdir,
                    (self.exporter._slack_service.team + "_" + channel_name + ".pdf"),
                ),
            )
            self.assertTrue(os.path.isfile(res_channel["filename_pdf"]))

            # assert export details are correct
            self.assertTrue(res_channel["ok"])
            self.assertEqual(res_channel["dest_path"], currentdir)
            self.assertEqual(res_channel["page_format"], "a4")
            self.assertEqual(res_channel["page_orientation"], "portrait")
            self.assertEqual(
                res_channel["max_messages"],
                settings.MAX_MESSAGES_PER_CHANNEL,
            )
            self.assertEqual(res_channel["timezone"], get_localzone())
            self.assertEqual(res_channel["locale"], babel.Locale.default())

            # assert infos in PDF file are correct
            pdf_file = open(res_channel["filename_pdf"], "rb")
            pdf_reader = PyPDF2.PdfFileReader(pdf_file)
            doc_info = pdf_reader.getDocumentInfo()
            self.assertEqual(doc_info.author, "Erik Kalkoken")
            self.assertEqual(doc_info.creator, f"Channel Export v{__version__}")
            self.assertEqual(
                doc_info.title,
                (self.exporter._slack_service.team + " / " + channel_name),
            )

    def test_run_with_args_1(self):
        # self.exporter._channel_names["G2234567X"] = "channel-exporter-run_with_args_1"
        response = self.exporter.run(
            ["G2234567X"], currentdir, None, None, "landscape", "a3", 42
        )
        self.assertTrue(response["ok"])
        self.assertIn("G2234567X", response["channels"])
        res_channel = response["channels"]["G2234567X"]

        # assert export details are correct
        self.assertTrue(res_channel["ok"])
        self.assertEqual(res_channel["message_count"], 4)
        self.assertEqual(res_channel["thread_count"], 0)
        self.assertEqual(res_channel["dest_path"], currentdir)
        self.assertEqual(res_channel["page_format"], "a3")
        self.assertEqual(res_channel["page_orientation"], "landscape")
        self.assertEqual(res_channel["max_messages"], 42)

    """
    def test_run_with_error(self):
        self.assertRaises(RuntimeError, self.exporter.run(
            ["channel-exporter"],
            "invalid_path"
        ))
    """

    def test_transform_text_user(self):
        self.assertEqual(
            self.exporter._transformer.transform_text("<@U62345678>", True),
            "<b>@Janet Hakuli</b>",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<@U999999999>", True),
            "<b>@user_U999999999</b>",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<@W999999999>", True),
            "<b>@user_W999999999</b>",
        )

    def test_transform_text_channel(self):
        self.assertEqual(
            self.exporter._transformer.transform_text("<#C72345678>", True),
            "<b>#tokio</b>",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<#C55555555>", True),
            "<b>#channel_C55555555</b>",
        )

    def test_transform_text_usergroup(self):
        self.assertEqual(
            self.exporter._transformer.transform_text("<!subteam^S72345678>", True),
            "<b>@marketing</b>",
        )

        self.assertEqual(
            self.exporter._transformer.transform_text("<!subteam^SAZ94GDB8>", True),
            "<b>@usergroup_SAZ94GDB8</b>",
        )

    def test_transform_text_special(self):
        self.assertEqual(
            self.exporter._transformer.transform_text("<!everyone>", True),
            "<b>@everyone</b>",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<!here>", True), "<b>@here</b>"
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<!channel>", True),
            "<b>@channel</b>",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text(
                "<!date^1392734382^Posted {date_num} {time_secs}"
                "|Posted 2014-02-18 6:39:42 AM PST>",
                True,
            ),
            self.exporter._locale_helper.get_datetime_formatted_str(1392734382),
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<!xyz>", True),
            "<b>@special_xyz</b>",
        )

    def test_transform_text_url(self):
        self.assertEqual(
            self.exporter._transformer.transform_text(
                "<https://www.google.com|Google>", True
            ),
            '<a href="https://www.google.com">Google</a>',
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<https://www.google.com>", True),
            '<a href="https://www.google.com">https://www.google.com</a>',
        )

    def test_transform_text_formatting(self):
        self.assertEqual(
            self.exporter._transformer.transform_text("*bold*", True), "<b>bold</b>"
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("_italic_", True), "<i>italic</i>"
        )
        self.assertEqual(
            self.exporter._transformer.transform_text(
                "text *bold* text _italic_ text", True
            ),
            "text <b>bold</b> text <i>italic</i> text",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("`code`", True),
            '<s fontfamily="NotoSansMono">code</s>',
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("*_bold+italic_*", True),
            "<b><i>bold+italic</i></b>",
        )

    def test_transform_text_general(self):
        self.assertEqual(
            self.exporter._transformer.transform_text(
                "some *text* <@U62345678> more text", True
            ),
            "some <b>text</b> <b>@Janet Hakuli</b> more text",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("first\nsecond\nthird", True),
            "first<br>second<br>third",
        )

        self.assertEqual(
            self.exporter._transformer.transform_text(
                "some text <@U62345678> more text", True
            ),
            "some text <b>@Janet Hakuli</b> more text",
        )

        self.assertEqual(
            self.exporter._transformer.transform_text(
                "before ident\n>indented text\nafter ident", True
            ),
            "before ident<br><blockquote>indented text</blockquote><br>after ident",
        )


class TestExporterTimezonesNLocale(NoSocketsTestCase):
    def setUp(self):
        workspace_info = {"team": "test", "user_id": "U9234567X"}
        user_names = {
            "U12345678": "Naoko Kobayashi",
            "U62345678": "Janet Hakuli",
            "U72345678": "Yuna Kobayashi",
            "U9234567X": "Erik Kalkoken",
        }

        channel_names = {
            "C12345678": "berlin",
            "C72345678": "tokio",
            "C42345678": "oslo",
            "G1234567X": "channel-exporter",
            "G2234567X": "channel-exporter-2",
        }

        usergroup_names = {
            "S12345678": "admins",
            "S72345678": "marketing",
            "S42345678": "sales",
        }

        self.exporter = SlackChannelExporter(
            "TEST", pytz.timezone("Asia/Bangkok"), babel.Locale.parse("es-MX", sep="-")
        )
        self.exporter._slack_service._workspace_info = workspace_info
        self.exporter._slack_service._user_names = user_names
        self.exporter._slack_service._channel_names = channel_names
        self.exporter._slack_service._usergroup_names = usergroup_names

    def test_timezone_locale(self):
        # self.exporter._channel_names["G2234567X"] = "channel-exporter-timezone-locale"
        channels = ["G2234567X"]
        response = self.exporter.run(channels, currentdir)
        self.assertTrue(response["ok"])
        res_channel = response["channels"]["G2234567X"]

        # assert export details are correct
        self.assertTrue(res_channel["ok"])
        self.assertEqual(
            res_channel["timezone"],
            pytz.timezone("Asia/Bangkok"),
        )
        self.assertEqual(res_channel["locale"], babel.Locale.parse("es-MX", sep="-"))

    def test_get_datetime(self):
        ts = 1006300923
        dt = self.exporter._locale_helper.get_datetime_from_ts(ts)
        self.assertEqual(dt.timestamp(), ts)

    def test_dummy(self):
        dt = datetime.utcnow()
        print(self.exporter._locale_helper.format_datetime_str(dt))
        print(self.exporter._locale_helper.get_datetime_formatted_str(dt.timestamp()))


"""
class TestExporterSlackMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.exporter = SlackChannelExporter(os.environ['SLACK_TOKEN'])

    def test_fetch_messages(self):
        oldest = parser.parse("2019-JUL-04")
        oldest = self.exporter._tz_local.localize(oldest)

        latest = parser.parse("2019-JUL-06")
        latest = self.exporter._tz_local.localize(latest)

        messages = self.exporter._fetch_messages_from_channel(
            channel_id="G7LULJD46",
            max_messages=1000
        )
        self.assertIsInstance(messages, list)

        messages = self.exporter._fetch_messages_from_channel(
            channel_id="G7LULJD46",
            max_messages=1000,
            oldest=oldest,
            latest=latest
        )
        self.assertIsInstance(messages, list)
"""


@patch("slackchannel2pdf.slack_service.slack")
@patch("slackchannel2pdf.slack_service.sleep", lambda x: None)
class TestSlackExporterFull(NoSocketsTestCase):
    """New test approach with API mocking, that allows full testing of the exporter"""

    def test_basic(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(team="T12345678")
        exporter = SlackChannelExporter("TOKEN_DUMMY")
        channels = ["C12345678"]
        # when
        response = exporter.run(channels, currentdir)
        # then
        self.assertTrue(response["ok"])

    def test_all_message_variants(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(team="T12345678")
        exporter = SlackChannelExporter("TOKEN_DUMMY")
        channels = ["G1234567X"]
        # when
        response = exporter.run(channels, currentdir)
        # then
        self.assertTrue(response["ok"])

    def test_team_name_invalid_characters(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(team="T92345678")
        exporter = SlackChannelExporter("TOKEN_DUMMY")
        channels = ["C12345678"]
        # when
        response = exporter.run(channels, currentdir)
        # then
        self.assertTrue(response["ok"])


if __name__ == "__main__":
    unittest.main()
