from ast import literal_eval
import configparser
from pathlib import Path

_FILE_NAME_BASE = "slackchannel2pdf"
_CONF_FILE_NAME = f"{_FILE_NAME_BASE}.ini"
_LOG_FILE_NAME = f"{_FILE_NAME_BASE}.log"


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


_parser = config_parser(
    defaults_path=Path(__file__).parent, home_path=Path.home(), cwd_path=Path.cwd()
)

# style and layout settings for PDF
PAGE_UNITS_DEFAULT = "mm"
FONT_FAMILY_DEFAULT = "NotoSans"
FONT_FAMILY_MONO_DEFAULT = "NotoSansMono"

PAGE_ORIENTATION_DEFAULT = _parser.getstr("pdf", "page_orientation")
PAGE_FORMAT_DEFAULT = _parser.getstr("pdf", "page_format")
FONT_SIZE_NORMAL = _parser.getint("pdf", "font_size_normal")
FONT_SIZE_LARGE = _parser.getint("pdf", "font_size_large")
FONT_SIZE_SMALL = _parser.getint("pdf", "font_size_small")
LINE_HEIGHT_DEFAULT = _parser.getint("pdf", "line_height_default")
LINE_HEIGHT_SMALL = _parser.getint("pdf", "line_height_small")
MARGIN_LEFT = _parser.getint("pdf", "margin_left")
TAB_WIDTH = _parser.getint("pdf", "tab_width")

# locale
FALLBACK_LOCALE = _parser.getstr("locale", "fallback_locale")

# slack
MINUTES_UNTIL_USERNAME_REPEATS = _parser.getint(
    "slack", "minutes_until_username_repeats"
)
MAX_MESSAGES_PER_CHANNEL = _parser.getint("slack", "max_messages_per_channel")
SLACK_PAGE_LIMIT = _parser.getint("slack", "slack_page_limit")

# define loggers
DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {"format": "[%(levelname)s] %(message)s"},
        "file": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "level": _parser.getstr("logging", "console_level"),
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
_file_log_path = _parser.getstr("logging", "file_path", fallback=None)
if _file_log_path:
    _file_log_path_full = Path(_file_log_path) / _LOG_FILE_NAME
    DEFAULT_LOGGING["handlers"]["file"] = {
        "level": _parser.getstr("logging", "file_level"),
        "formatter": "file",
        "class": "logging.FileHandler",
        "filename": str(_file_log_path_full),
        "mode": "a",
    }
    DEFAULT_LOGGING["loggers"][""]["handlers"].append("file")
