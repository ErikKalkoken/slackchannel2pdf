import configparser
import pickle
import tempfile
import unittest
from pathlib import Path

from slackchannel2pdf import settings


def deepcopy(config: configparser.ConfigParser) -> configparser.ConfigParser:
    """deep copy config"""
    rep = pickle.dumps(config)
    new_config = pickle.loads(rep)
    return new_config


class TestConvertStr(unittest.TestCase):
    def test_should_convert_string(self):
        self.assertEqual(settings._configparser_convert_str('"abc"'), "abc")

    def test_should_raise_exception_when_not_str(self):
        with self.assertRaises(configparser.ParsingError):
            settings._configparser_convert_str("42")


def fetch_default_config() -> configparser.ConfigParser:
    default_config = configparser.ConfigParser(
        converters={"str": settings._configparser_convert_str}
    )
    default_config.read(settings._DEFAULTS_PATH / settings._CONF_FILE_NAME)
    return default_config


class TestConfigParser(unittest.TestCase):

    TEST_SECTION = "pdf"
    TEST_OPTION = "font_size_normal"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.default_config = fetch_default_config()
        cls.default_config.set(cls.TEST_SECTION, cls.TEST_OPTION, "12")

    def test_should_return_default_configuration(self):
        # given
        defaults_path = Path(tempfile.mkdtemp())
        default_file_path = defaults_path / settings._CONF_FILE_NAME
        with default_file_path.open("w", encoding=("utf-8")) as fp:
            self.default_config.write(fp)
        # when
        new_parser = settings.config_parser(defaults_path)
        # then
        self.assertEqual(new_parser.getint(self.TEST_SECTION, self.TEST_OPTION), 12)

    def test_should_return_home_configuration(self):
        # given
        defaults_path = Path(tempfile.mkdtemp())
        file_path = defaults_path / settings._CONF_FILE_NAME
        with file_path.open("w", encoding=("utf-8")) as fp:
            self.default_config.write(fp)
        home_path = Path(tempfile.mkdtemp())
        home_config = deepcopy(self.default_config)
        home_config.set(self.TEST_SECTION, self.TEST_OPTION, "10")
        file_path = home_path / settings._CONF_FILE_NAME
        with file_path.open("w", encoding=("utf-8")) as fp:
            home_config.write(fp)
        # when
        new_parser = settings.config_parser(
            defaults_path=defaults_path, home_path=home_path
        )
        # then
        self.assertEqual(new_parser.getint(self.TEST_SECTION, self.TEST_OPTION), 10)

    def test_should_return_cwd_configuration(self):
        # given
        defaults_path = Path(tempfile.mkdtemp())
        file_path = defaults_path / settings._CONF_FILE_NAME
        with file_path.open("w", encoding=("utf-8")) as fp:
            self.default_config.write(fp)
        home_path = Path(tempfile.mkdtemp())
        home_config = deepcopy(self.default_config)
        home_config.set(self.TEST_SECTION, self.TEST_OPTION, "10")
        file_path = home_path / settings._CONF_FILE_NAME
        with file_path.open("w", encoding=("utf-8")) as fp:
            home_config.write(fp)
        cwd_path = Path(tempfile.mkdtemp())
        cwd_config = deepcopy(self.default_config)
        cwd_config.set(self.TEST_SECTION, self.TEST_OPTION, "8")
        file_path = cwd_path / settings._CONF_FILE_NAME
        with file_path.open("w", encoding=("utf-8")) as fp:
            cwd_config.write(fp)
        # when
        new_parser = settings.config_parser(
            defaults_path=defaults_path, home_path=home_path, cwd_path=cwd_path
        )
        # then
        self.assertEqual(new_parser.getint(self.TEST_SECTION, self.TEST_OPTION), 8)


class TestSettings(unittest.TestCase):
    def test_should_set_console_log_level(self):
        # given
        config = fetch_default_config()
        config.set("logging", "console_log_level", '"DEBUG"')
        # when
        dict_config = settings.setup_logging(config)
        # then
        self.assertEqual(dict_config["handlers"]["console"]["level"], "DEBUG")

    def test_should_set_file_log_level(self):
        # given
        config = fetch_default_config()
        config.set("logging", "log_file_enabled", "True")
        config.set("logging", "file_log_level", '"DEBUG"')
        # when
        dict_config = settings.setup_logging(config)
        # then
        self.assertEqual(dict_config["handlers"]["file"]["level"], "DEBUG")

    def test_should_enable_file_logger(self):
        # given
        config = fetch_default_config()
        config.set("logging", "log_file_enabled", "True")
        # when
        dict_config = settings.setup_logging(config)
        # then
        self.assertIn("file", dict_config["handlers"])
        self.assertIn("file", dict_config["loggers"][""]["handlers"])

    def test_should_disable_file_logger(self):
        # given
        config = fetch_default_config()
        config.set("logging", "log_file_enabled", "False")
        # when
        dict_config = settings.setup_logging(config)
        # then
        self.assertNotIn("file", dict_config["handlers"])
        self.assertNotIn("file", dict_config["loggers"][""]["handlers"])

    def test_should_set_log_file_path(self):
        # given
        config = fetch_default_config()
        config.set("logging", "log_file_enabled", "True")
        my_path = Path(tempfile.mkdtemp())
        config.set("logging", "log_file_path", f"'{str(my_path)}'")
        # when
        dict_config = settings.setup_logging(config)
        # then
        self.assertEqual(
            Path(dict_config["handlers"]["file"]["filename"]).parent, my_path
        )
