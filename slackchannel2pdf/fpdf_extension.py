"""This module contains an extended FPDF class with rudimentary HTML support."""

import logging
import os
import re

import fpdf_mod

from . import settings

logger = logging.getLogger(__name__)

fpdf_mod.set_global("FPDF_CACHE_MODE", 1)
fpdf_mod.set_global("SYSTEM_TTFONTS", os.path.join(os.path.dirname(__file__), "fonts"))


class HtmlConversionError(Exception):
    """A HTML conversion error."""


class FPDFext(fpdf_mod.FPDF):
    """This class extends FDPF to enable formatting with rudimentary HTML

    This package extends the FPDF class with the functionality to use
    rudimentary HTML for defining text formatting with the new
    method write_html()

    The class is based on the example in Tutorial 6 from
    the official FPDF documentation (http://www.fpdf.org/)
    but has extended functionality

    It's build upon the pyfpdf variant from this github:
    https://github.com/alexanderankin/pyfpdf

    Currently supports: <b>, <i>, <u>, <a>, <br>, <blockquote> <s>

    <s> is a custom tag for setting the font for part of a text. Example:
    <s fontfamily="Courier" size="14" style="B">
    Attributes can be omitted and wil then not be set.

    Unsupported tags are ignored and removed from the text
    """

    _TAB_WIDTH = 4
    _TAGS_SUPPORTED = ["b", "i", "u", "a", "br", "blockquote", "s"]

    def __init__(self, orientation="P", unit="mm", page_format="A4"):
        super().__init__(orientation=orientation, unit=unit, format=page_format)
        self._tags = {}
        self._tags["B"] = 0
        self._tags["I"] = 0
        self._tags["U"] = 0
        self._tags["BLOCKQUOTE"] = 0
        self._href = ""
        self._last_font = None

    def write_html(self, height, html):
        """write() with support for rudimentary formatting with HTML tags"""
        html = html.replace("\n", " ")

        # split html into parts to identify all HTML tags
        # even numbered parts will contain text
        # odd numbered parts will contain tags
        parts = re.split(r"<([^>]*)>", html)

        # run through all parts one by one
        try:
            for i, part in dict(enumerate(parts)).items():
                if i % 2 == 0:
                    # we have text
                    if len(self._href) > 0:
                        self._put_link(self._href, height, part)
                    else:
                        self.write(height, part)

                else:
                    # we have a tag
                    if part[0] == "/":
                        self._close_tag(part[1 : len(part)].upper())
                    else:
                        # extract all attributes from the current tag if any
                        tag_parts = part.split(" ")
                        tag = tag_parts.pop(0).upper()
                        attributes = {}
                        for tag_part in tag_parts:
                            match_obj = re.search(r'([^=]*)=["\']?([^"\']*)', tag_part)
                            if match_obj is not None and len(match_obj.groups()) == 2:
                                attributes[
                                    match_obj.group(1).upper()
                                ] = match_obj.group(2)

                        self._open_tag(tag, attributes)

        except HtmlConversionError:
            logger.error("Failed to convert HTML to PDF: %s" % html)

    def _open_tag(self, tag, attributes):
        """set style for opening tags and singular tags"""

        if tag in ["B", "I", "U"]:
            self._set_style(tag, True)

        if tag == "BLOCKQUOTE":
            self._set_ident_plus()

        if tag == "A":
            self._href = attributes["HREF"]

        if tag == "BR":
            self.ln(5)

        if tag == "S":
            if self._last_font is not None:
                raise HtmlConversionError("<s> tags can not be nested")

            self._last_font = {
                "font_family": self.font_family,
                "size": self.font_size_pt,
                "style": self.font_style,
            }

            if "FONTFAMILY" in attributes:
                font_family = attributes["FONTFAMILY"]
            else:
                font_family = self.font_family

            if "SIZE" in attributes:
                size = int(attributes["SIZE"])
            else:
                size = self.font_size_pt

            if "STYLE" in attributes:
                style = attributes["STYLE"]
            else:
                style = self.font_style

            self.set_font(font_family, size=size, style=style)

    def _close_tag(self, tag):
        """set style for closing tags"""

        if tag in ["B", "I", "U"]:
            self._set_style(tag, False)

        if tag == "BLOCKQUOTE":
            self._set_ident_minus()

        if tag == "A":
            self._href = ""

        if tag == "S":
            if self._last_font is not None:
                self.set_font(
                    self._last_font["font_family"],
                    size=self._last_font["size"],
                    style=self._last_font["style"],
                )
                self._last_font = None

    def _set_style(self, tag, enable):
        """set the actual font style based on input"""
        self._tags[tag] += 1 if enable else -1
        style = ""
        for my_style in ["B", "I", "U"]:
            if self._tags[my_style] > 0:
                style += my_style

        self.set_font(self.font_family, size=self.font_size_pt, style=style)

    def _set_ident_plus(self):
        """moves current left margin and position forward by tab width"""
        self.set_left_margin(self.l_margin + self._TAB_WIDTH)
        self.set_x(self.get_x() + self._TAB_WIDTH)
        self.ln()

    def _set_ident_minus(self):
        """reduces current left margin and position forward by tab width"""
        left_margin = self.l_margin
        my_x = self.get_x()
        if left_margin > self._TAB_WIDTH and my_x > self._TAB_WIDTH:
            self.set_left_margin(left_margin - self._TAB_WIDTH)
            self.set_x(my_x - self._TAB_WIDTH)
            self.ln()

    def _put_link(self, url, height, txt):
        """set style and write text to create a link"""
        self.set_text_color(0, 0, 255)
        self._set_style("U", True)
        self.write(height, txt, url)
        self._set_style("U", False)
        self.set_text_color(0)


class MyFPDF(FPDFext):
    """Inheritance of FPDF class to add header and footers and set PDF settings"""

    def __init__(self, orientation="P", unit="mm", page_format="A4"):
        super().__init__(orientation=orientation, unit=unit, page_format=page_format)
        self._page_title = ""

    @property
    def page_title(self):
        """text shown as title on every page"""
        return self._page_title

    @page_title.setter
    def page_title(self, text):
        """set text to appear as title on every page"""
        self._page_title = str(text)

    def header(self):
        """definition of custom header"""
        self.set_font(
            settings.FONT_FAMILY_DEFAULT, size=settings.FONT_SIZE_NORMAL, style="B"
        )
        self.cell(0, 0, self._page_title, 0, 1, "C")
        self.ln(settings.LINE_HEIGHT_DEFAULT)

    def footer(self):
        """definition of custom footer"""
        self.set_y(-15)
        self.cell(0, 10, "Page " + str(self.page_no()) + " / {nb}", 0, 0, "C")

    def write_info_table(self, table_def):
        """write info table defined by dict"""
        cell_height = 10
        for key, value in table_def.items():
            self.set_font(self.font_family, style="B")
            self.cell(50, cell_height, str(key), 1)
            self.set_font(self.font_family)
            self.cell(0, cell_height, str(value), 1)
            self.ln()
