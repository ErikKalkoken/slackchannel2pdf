# Copyright 2019 Erik Kalkoken
#
# Licensed under MIT license. See attached file for details
#
# This package contains the implementation of an extended FPDF class
# with rudimentary HTML support
#

import fpdf_mod
import re
import os

fpdf_mod.set_global("FPDF_CACHE_MODE", 1)
fpdf_mod.set_global("SYSTEM_TTFONTS", os.path.join(os.path.dirname(__file__), "fonts"))


class FPDF_ext(fpdf_mod.FPDF):
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
        self._tags = dict()
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
                    attributes = dict()
                    for tag_part in tag_parts:
                        match_obj = re.search(r'([^=]*)=["\']?([^"\']*)', tag_part)
                        if match_obj is not None and len(match_obj.groups()) == 2:
                            attributes[match_obj.group(1).upper()] = match_obj.group(2)

                    self._open_tag(tag, attributes)

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
                raise RuntimeError("<s> tags can not be nested")

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
        for s in ["B", "I", "U"]:
            if self._tags[s] > 0:
                style += s

        self.set_font(self.font_family, size=self.font_size_pt, style=style)

    def _set_ident_plus(self):
        """moves current left margin and position forward by tab width"""
        self.set_left_margin(self.l_margin + self._TAB_WIDTH)
        self.set_x(self.get_x() + self._TAB_WIDTH)
        self.ln()

    def _set_ident_minus(self):
        """reduces current left margin and position forward by tab width"""
        left_margin = self.l_margin
        x = self.get_x()
        if left_margin > self._TAB_WIDTH and x > self._TAB_WIDTH:
            self.set_left_margin(left_margin - self._TAB_WIDTH)
            self.set_x(x - self._TAB_WIDTH)
            self.ln()

    def _put_link(self, url, height, txt):
        """ set style and write text to create a link"""
        self.set_text_color(0, 0, 255)
        self._set_style("U", True)
        self.write(height, txt, url)
        self._set_style("U", False)
        self.set_text_color(0)
