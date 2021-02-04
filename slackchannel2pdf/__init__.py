import logging.config
from . import settings

logging.config.dictConfig(settings.DEFAULT_LOGGING)

__version__ = "1.2.3"
