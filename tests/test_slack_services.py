import unittest
from unittest.mock import patch

from slackchannel2pdf.slack_service import SlackService
from . import SlackClientStub


class TestExporterReduceToDict(unittest.TestCase):
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


class TestFetchChannelNames(unittest.TestCase):
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
