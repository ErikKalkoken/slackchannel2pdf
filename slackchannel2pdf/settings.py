"""Defines all global settings incl. from configuration files"""

import configparser
from ast import literal_eval
from pathlib import Path

_FILE_NAME_BASE = "slackchannel2pdf"
_CONF_FILE_NAME = f"{_FILE_NAME_BASE}.ini"
_LOG_FILE_NAME = f"{_FILE_NAME_BASE}.log"

_DEFAULTS_PATH = Path(__file__).parent


def _configparser_convert_str(x):
    result = literal_eval(x)
    if not isinstance(result, str):
        raise configparser.ParsingError(f"Needs to be a string type: {x}")
    return result


def config_parser(
    defaults_path: Path, home_path: Path = None, cwd_path: Path = None
) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(converters={"str": _configparser_convert_str})
    config_file_paths = [defaults_path / _CONF_FILE_NAME]
    if home_path:
        config_file_paths.append(home_path / _CONF_FILE_NAME)
    if cwd_path:
        config_file_paths.append(cwd_path / _CONF_FILE_NAME)
    found = parser.read(config_file_paths)
    if not found:
        raise RuntimeError("Can not find a configuration file anywhere")
    return parser


_my_config = config_parser(
    defaults_path=_DEFAULTS_PATH, home_path=Path.home(), cwd_path=Path.cwd()
)

# style and layout settings for PDF
PAGE_UNITS_DEFAULT = "mm"
FONT_FAMILY_DEFAULT = "NotoSans"
FONT_FAMILY_MONO_DEFAULT = "NotoSansMono"

PAGE_ORIENTATION_DEFAULT = _my_config.getstr("pdf", "page_orientation")
PAGE_FORMAT_DEFAULT = _my_config.getstr("pdf", "page_format")
FONT_SIZE_NORMAL = _my_config.getint("pdf", "font_size_normal")
FONT_SIZE_LARGE = _my_config.getint("pdf", "font_size_large")
FONT_SIZE_SMALL = _my_config.getint("pdf", "font_size_small")
LINE_HEIGHT_DEFAULT = _my_config.getint("pdf", "line_height_default")
LINE_HEIGHT_SMALL = _my_config.getint("pdf", "line_height_small")
MARGIN_LEFT = _my_config.getint("pdf", "margin_left")
TAB_WIDTH = _my_config.getint("pdf", "tab_width")

# locale
FALLBACK_LOCALE = _my_config.getstr("locale", "fallback_locale")

# slack
MINUTES_UNTIL_USERNAME_REPEATS = _my_config.getint(
    "slack", "minutes_until_username_repeats"
)
MAX_MESSAGES_PER_CHANNEL = _my_config.getint("slack", "max_messages_per_channel")
SLACK_PAGE_LIMIT = _my_config.getint("slack", "slack_page_limit")


def setup_logging(config: configparser.ConfigParser) -> None:
    config_logging = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {"format": "[%(levelname)s] %(message)s"},
            "file": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "console": {
                "level": config.getstr("logging", "console_log_level"),
                "formatter": "console",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",  # Default is stderr
            }
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }

    # add log file if configured
    log_file_enabled = config.getboolean("logging", "log_file_enabled", fallback=False)
    if log_file_enabled:
        file_log_path_full = config.getstr("logging", "log_file_path", fallback=None)
        filename = (
            Path(file_log_path_full) / _LOG_FILE_NAME
            if file_log_path_full
            else _LOG_FILE_NAME
        )
        config_logging["handlers"]["file"] = {
            "level": config.getstr("logging", "file_log_level"),
            "formatter": "file",
            "class": "logging.FileHandler",
            "filename": filename,
            "mode": "a",
        }
        config_logging["loggers"][""]["handlers"].append("file")
    return config_logging


DEFAULT_LOGGING = setup_logging(_my_config)
