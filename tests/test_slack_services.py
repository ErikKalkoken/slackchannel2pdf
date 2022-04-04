from unittest.mock import patch

from slackchannel2pdf.slack_service import SlackService

from .helpers.no_sockets import NoSocketsTestCase
from .helpers.slack_client_stub import SlackClientStub

MODULE_NAME = "slackchannel2pdf.slack_service"


class TestReduceToDict(NoSocketsTestCase):
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


@patch(MODULE_NAME + ".slack_sdk")
class TestSlackService(NoSocketsTestCase):
    def test_should_return_all_user_names_1(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(team="T12345678")
        slack_service = SlackService("TEST")
        # when
        result = slack_service.fetch_user_names()
        # then
        self.assertDictEqual(
            {
                "U12345678": "Naoko Kobayashi",
                "U62345678": "Janet Hakuli",
                "U72345678": "Yuna Kobayashi",
                "U92345678": "Rosie Dunbar",
                "U9234567X": "Erik Kalkoken",
            },
            result,
        )

    def test_should_return_all_user_names_2(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(
            team="T12345678", page_size=2
        )
        slack_service = SlackService("TOKEN_DUMMY")
        # when
        result = slack_service.fetch_user_names()
        # then
        self.assertDictEqual(
            {
                "U12345678": "Naoko Kobayashi",
                "U62345678": "Janet Hakuli",
                "U72345678": "Yuna Kobayashi",
                "U92345678": "Rosie Dunbar",
                "U9234567X": "Erik Kalkoken",
            },
            result,
        )

    def test_should_return_all_conversations_1(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(team="T12345678")
        slack_service = SlackService("TEST")
        # when
        result = slack_service._fetch_channel_names()
        # then
        self.assertDictEqual(
            {
                "C12345678": "berlin",
                "C42345678": "oslo",
                "C72345678": "london",
                "C92345678": "moscow",
                "G1234567X": "bangkok",
                "G2234567X": "tokyo",
            },
            result,
        )

    def test_should_return_all_conversations_2(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(
            team="T12345678", page_size=2
        )
        slack_service = SlackService("TEST")
        # when
        result = slack_service._fetch_channel_names()
        # then
        self.assertDictEqual(
            {
                "C12345678": "berlin",
                "C42345678": "oslo",
                "C72345678": "london",
                "C92345678": "moscow",
                "G1234567X": "bangkok",
                "G2234567X": "tokyo",
            },
            result,
        )

    def test_should_return_all_messages_from_conversation_1(self, mock_slack):
        # given
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

    def test_should_return_all_messages_from_conversation_2(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(
            team="T12345678", page_size=2
        )
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

    def test_should_return_all_threads_from_messages(self, mock_slack):
        # given
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
