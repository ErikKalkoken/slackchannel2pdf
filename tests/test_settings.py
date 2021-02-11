import configparser
from pathlib import Path
import unittest
import tempfile

from slackchannel2pdf import settings


class TestConvertStr(unittest.TestCase):
    def test_should_convert_string(self):
        self.assertEqual(settings._configparser_convert_str('"abc"'), "abc")

    def test_should_raise_exception_when_not_str(self):
        with self.assertRaises(configparser.ParsingError):
            settings._configparser_convert_str("42")


class TestConfigParser(unittest.TestCase):
    def test_should_return_default_configuration(self):
        # given
        default_config = configparser.ConfigParser()
        default_config.read(Path(__file__).parent / "config.ini")
        defaults_path = Path(tempfile.mkdtemp())
        default_file_path = defaults_path / settings._CONF_FILE_NAME
        with default_file_path.open("w", encoding=("utf-8")) as fp:
            default_config.write(fp)
        # when
        new_parser = settings.config_parser(defaults_path)
        # then
        self.assertEqual(new_parser.getint("pdf", "font_size_normal"), 12)

    def test_should_return_home_configuration(self):
        # given
        default_config = configparser.ConfigParser()
        default_config.read(Path(__file__).parent / "config.ini")
        defaults_path = Path(tempfile.mkdtemp())
        file_path = defaults_path / settings._CONF_FILE_NAME
        with file_path.open("w", encoding=("utf-8")) as fp:
            default_config.write(fp)
        home_path = Path(tempfile.mkdtemp())
        file_path = home_path / settings._CONF_FILE_NAME
        default_config.set("pdf", "font_size_normal", "10")
        with file_path.open("w", encoding=("utf-8")) as fp:
            default_config.write(fp)
        # when
        new_parser = settings.config_parser(
            defaults_path=defaults_path, home_path=home_path
        )
        # then
        self.assertEqual(new_parser.getint("pdf", "font_size_normal"), 10)
