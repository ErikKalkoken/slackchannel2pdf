import unittest

from slackchannel2pdf import helpers


class TestTransformEncoding(unittest.TestCase):
    def test_should_transform_special_chars(self):
        self.assertEqual(helpers.transform_encoding("special char ✓"), "special char ✓")
        self.assertEqual(helpers.transform_encoding("&lt;"), "<")
        self.assertEqual(helpers.transform_encoding("&#60;"), "<")
