import logging
import html
import json
from pathlib import Path


logger = logging.getLogger(__name__)


def transform_encoding(text: str) -> str:
    """adjust encoding to latin-1 and transform HTML entities"""
    text2 = html.unescape(text)
    text2 = text2.encode("utf-8", "replace").decode("utf-8")
    text2 = text2.replace("\t", "    ")
    return text2


def read_array_from_json_file(filepath: Path, quiet=False) -> list:
    """reads a json file and returns its contents as array"""
    my_file = filepath.parent / (filepath.name + ".json")
    if not my_file.is_file:
        if quiet is False:
            logger.warning("file does not exist: %s", filepath)
        arr = list()
    else:
        try:
            with my_file.open("r", encoding="utf-8") as f:
                arr = json.load(f)
        except IOError:
            if quiet is False:
                logger.warning("failed to read from %s: ", my_file, exc_info=True)
            arr = list()

    return arr


def write_array_to_json_file(arr, filepath: Path) -> None:
    """writes array to a json file"""
    my_file = filepath.parent / (filepath.name + ".json")
    logger.info("Writing file: %s", filepath)
    try:
        with my_file.open("w", encoding="utf-8") as f:
            json.dump(arr, f, sort_keys=True, indent=4, ensure_ascii=False)
    except IOError:
        logger.error("failed to write to %s", my_file, exc_info=True)
