# Copyright (C) 2019 Erik Kalkoken
#
# This package extends the FPDF class with the functionality to use 
# rudimentary HTML for defining text formatting
#
# It is a port from the example in Tutorial 6 from 
# the official FPDF documentation (http://www.fpdf.org/)
# with some minor changes to improve readability and extensibility
#
# It's build upon this pyfpdf variant: https://github.com/alexanderankin/pyfpdf

from fpdf import FPDF
import re

""" 
This class extends FDPF to add the new method write_html()
"""
class FDPF_ext(FPDF):
    
    def __init__(self, orientation='P', unit='mm', format='A4'):        
        super().__init__(orientation=orientation, unit=unit, format=format)
        self._tags = dict()
        self._tags["B"] = 0
        self._tags["I"] = 0
        self._tags["U"] = 0
        self._href = ""
            

    def write_html(self, height, html):
        """ write text with HTML tags for formatting  """
        html = html.replace("\n"," ")
        
        # split html into parts to identify all HTML tags
        # even numbered parts will contain text
        # odd numbered parts will contain tags
        parts = re.split(r'<([^>]*)>', html)
        
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
                    self._close_tag(part[1:len(part)].upper())
                else:
                    # extract all attributes from the current tag if any
                    tag_parts = part.split(" ")
                    tag = tag_parts.pop(0).upper()
                    attributes = dict()                    
                    for tag_part in tag_parts:
                        matchObj = re.search(r'([^=]*)=["\']?([^"\']*)', tag_part)
                        if len(matchObj.groups()) == 2:
                            attributes[matchObj.group(1).upper()] = matchObj.group(2)
                            
                    
                    self._open_tag(tag, attributes)
            

    def _open_tag(self, tag, attributes):
        """ set style for opening tags and singular tags  """
        if tag == "B" or tag == "I" or tag == "U":
            self._set_style(tag, True)
        if tag == "A":
            self._href = attributes["HREF"]
        if tag == "BR":
            self.ln(5)

    
    def _close_tag(self, tag):
        """ set style for closing tags  """
        if tag == "B" or tag == "I" or tag == "U":
            self._set_style(tag, False)
        if tag == "A":
            self._href = ""


    def _set_style(self, tag, enable):
        """ set the actual font style based on input  """
        self._tags[tag] += 1 if enable else -1
        style = ""
        for s in ["B", "I", "U"]:
            if self._tags[s] > 0:
                style += s

        self.set_font(self.font_family, size=self.font_size_pt, style=style)

    def _put_link(self, url, height, txt):
        """ set style and write text to create a link  """
        self.set_text_color(0, 0, 255)
        self._set_style("U", True)
        self.write(height, txt, url)
        self._set_style("U", False)
        self.set_text_color(0)


def main():
    
    html = """You can now easily print text mixing different styles: <b>bold</b>, <i>italic</i>, <u>underlined</u>, or <b><i><u>all at once</u></i></b>!<br><br>You can also insert links on text, such as <a href="http://www.fpdf.org" blank="_target">www.fpdf.org</a>, or on an image: click on the logo."""
    
    document = FDPF_ext()
    document.add_page()
    document.set_font('Arial', size=12)
    document.cell(w=0, txt="hello world")
    document.write_html(5, html)
    document.output("hello_world.pdf")


if __name__ == '__main__':
    main()        