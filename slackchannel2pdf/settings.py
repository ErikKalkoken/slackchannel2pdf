# style and layout settings for PDF
PAGE_ORIENTATION_DEFAULT = "portrait"
PAGE_FORMAT_DEFAULT = "a4"
PAGE_UNITS_DEFAULT = "mm"
FONT_FAMILY_DEFAULT = "NotoSans"
FONT_FAMILY_MONO_DEFAULT = "NotoSansMono"
FONT_SIZE_NORMAL = 12
FONT_SIZE_LARGE = 14
FONT_SIZE_SMALL = 10
LINE_HEIGHT_DEFAULT = 6
LINE_HEIGHT_SMALL = 2
MARGIN_LEFT = 10
TAB_WIDTH = 4

# locale
FALLBACK_LOCALE = "en"

# slack
MINUTES_UNTIL_USERNAME_REPEATS = 10
MAX_MESSAGES_PER_CHANNEL = 10000
SLACK_PAGE_LIMIT = 200

# logging
DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {"format": "[%(levelname)s] %(message)s"},
        "file": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "formatter": "console",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # Default is stderr
        },
        # "file": {
        #     "level": "INFO",
        #     "formatter": "file",
        #     "class": "logging.FileHandler",
        #     "filename": "slackchannel2pdf.log",
        #     "mode": "a",
        # },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
