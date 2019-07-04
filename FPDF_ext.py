from fpdf import FPDF
import re

class FDPF_ext(FPDF):
    
    def __init__(self, orientation='P', unit='mm', format='A4'):        
        super().__init__(orientation=orientation, unit=unit, format=format)
        self._tags = dict()
        self._tags["B"] = 0
        self._tags["I"] = 0
        self._tags["U"] = 0
        self._href = ""
            

    def write_html(self, height, html):        
        html = html.replace("\n"," ")
        parts = re.split(r'<([^>]*)>', html)
        
        for i, part in dict(enumerate(parts)).items():
            if i % 2 == 0:
                # even parts contain text
                if len(self._href) > 0:
                    self._put_link(self._href, height, part)
                else:
                    self.write(height, part)

            else:
                # odd parts contain a tag
                if part[0] == "/":
                    self._close_tag(part[1:len(part)].upper())
                else:
                    # extract attributes if any
                    tag_parts = part.split(" ")
                    tag = tag_parts.pop(0).upper()
                    attr = dict()                    
                    for v in tag_parts:
                        attr_list = re.findall(r'([^=]*)=["\']?([^"\']*)', v)
                        if len(attr_list) > 0:
                            for x in attr_list:
                                attr[x[0].upper()] = x[1]
                    
                    self._open_tag(tag, attr)
            

    def _open_tag(self, tag, attr):
        # opening tag
        if tag == "B" or tag == "I" or tag == "U":
            self._set_style(tag, True)
        if tag == "A":
            self._href = attr["HREF"]
        if tag == "BR":
            self.ln(5)

    
    def _close_tag(self, tag):
        # closing tag
        if tag == "B" or tag == "I" or tag == "U":
            self._set_style(tag, False)
        if tag == "A":
            self._href = ""


    def _set_style(self, tag, enable):
        self._tags[tag] += 1 if enable else -1
        style = ""
        for s in ["B", "I", "U"]:
            if self._tags[s] > 0:
                style += s

        self.set_font(self.font_family, size=self.font_size_pt, style=style)

    def _put_link(self, url, height, txt):
        self.set_text_color(0, 0, 255)
        self._set_style("U", True)
        self.write(height, txt, url)
        self._set_style("U", False)
        self.set_text_color(0)


def main():
    
    html = """You can now easily print text mixing different styles: <b>bold</b>, <i>italic</i>, <u>underlined</u>, or <b><i><u>all at once</u></i></b>!<br><br>You can also insert links on text, such as <a href="http://www.fpdf.org">www.fpdf.org</a>, or on an image: click on the logo."""
    
    document = FDPF_ext()
    document.add_page()
    document.set_font('Arial', size=12)
    document.cell(w=0, txt="hello world")
    document.write_html(5, html)
    document.output("hello_world.pdf")


if __name__ == '__main__':
    main()        