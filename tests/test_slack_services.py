from unittest.mock import patch

from slackchannel2pdf.slack_service import SlackService
from .testtools import SlackClientStub
from .no_sockets import NoSocketsTestCase


class TestExporterReduceToDict(NoSocketsTestCase):
    def setUp(self):
        self.a = [
            {"id": "1", "name_1": "Naoko Kobayashi", "name_2": "naoko.kobayashi"},
            {"id": "2", "name_1": "Janet Hakuli", "name_2": "janet.hakuli"},
            {"id": "3", "name_2": "rosie.dunbar"},
            {"id": "4"},
            {"name_1": "John Doe", "name_2": "john.doe"},
        ]

    def test_1(self):
        expected = {"1": "Naoko Kobayashi", "2": "Janet Hakuli"}
        result = SlackService._reduce_to_dict(self.a, "id", "name_1")
        self.assertEqual(result, expected)

    def test_2(self):
        expected = {"1": "Naoko Kobayashi", "2": "Janet Hakuli", "3": "rosie.dunbar"}
        result = SlackService._reduce_to_dict(self.a, "id", "name_1", "name_2")
        self.assertEqual(result, expected)

    def test_3(self):
        expected = {"1": "naoko.kobayashi", "2": "janet.hakuli", "3": "rosie.dunbar"}
        result = SlackService._reduce_to_dict(self.a, "id", "invalid_col", "name_2")
        self.assertEqual(result, expected)


class TestFetchChannelNames(NoSocketsTestCase):
    def test_should_return_all_names(self):
        # given
        with patch("slackchannel2pdf.slack_service.slack") as mock_slack:
            mock_slack.WebClient.return_value = SlackClientStub(team="T12345678")
            slack_service = SlackService("TOKEN_DUMMY")
        # when
        result = slack_service.channel_names()
        # then
        self.assertDictEqual(
            {
                "C12345678": "berlin",
                "C42345678": "oslo",
                "C72345678": "london",
                "G1234567X": "bangkok",
                "G2234567X": "tokyo",
            },
            result,
        )

    """

    def test_should_return_all_names_paging(self):
        # given
        with patch("slackchannel2pdf.slack_service.slack") as mock_slack:
            mock_slack.WebClient.return_value = SlackClientStub(
                team="T12345678", page_size=2
            )
            slack_service = SlackService("TOKEN_DUMMY")
        # when
        result = slack_service.channel_names()
        # then
        self.assertDictEqual(
            {
                "C12345678": "berlin",
                "C42345678": "oslo",
                "C72345678": "london",
                "G1234567X": "bangkok",
                "G2234567X": "tokyo",
            },
            result,
        )
    """


class TestFetchMessagesFromChannel(NoSocketsTestCase):
    def test_should_return_all_message_no_paging(self):
        # given
        with patch("slackchannel2pdf.slack_service.slack") as mock_slack:
            mock_slack.WebClient.return_value = SlackClientStub(team="T12345678")
            slack_service = SlackService("TEST")
            slack_service._channel_names = {"C72345678": "dummy"}
        # when
        result = slack_service.fetch_messages_from_channel("C72345678", 200)
        # then
        ids = {message["ts"] for message in result}
        self.assertSetEqual(
            ids,
            {
                "1562274541.000800",
                "1562274542.000800",
                "1562274543.000800",
                "1562274544.000800",
                "1562274545.000800",
            },
        )

    def test_should_return_all_message_with_paging(self):
        # given
        with patch("slackchannel2pdf.slack_service.slack") as mock_slack:
            mock_slack.WebClient.return_value = SlackClientStub(
                team="T12345678", page_size=2
            )
            slack_service = SlackService("TEST")
            slack_service._channel_names = {"C72345678": "dummy"}
        # when
        with patch("slackchannel2pdf.slack_service.sleep", lambda x: None):
            result = slack_service.fetch_messages_from_channel("C72345678", 200)
        # then
        ids = {message["ts"] for message in result}
        self.assertSetEqual(
            ids,
            {
                "1562274541.000800",
                "1562274542.000800",
                "1562274543.000800",
                "1562274544.000800",
                "1562274545.000800",
            },
        )


class TestFetchThreadsFromMessages(NoSocketsTestCase):
    def test_should_return_all_threads(self):
        # given
        with patch("slackchannel2pdf.slack_service.slack") as mock_slack:
            slack_stub = SlackClientStub(team="T12345678", page_size=2)
            mock_slack.WebClient.return_value = slack_stub
            slack_service = SlackService("TEST")
            slack_service._channel_names = {"G1234567X": "dummy"}
        messages = slack_stub._slack_data["T12345678"]["conversations_history"][
            "G1234567X"
        ]
        # when
        result = slack_service.fetch_threads_from_messages("G1234567X", messages, 200)
        # then
        self.assertIn("1561764011.015500", result)
        ids = {message["ts"] for message in result["1561764011.015500"]}
        self.assertSetEqual(
            ids,
            {
                "1561764011.015500",
                "1562171321.000100",
                "1562171322.000100",
                "1562171323.000100",
                "1562171324.000100",
            },
        )
