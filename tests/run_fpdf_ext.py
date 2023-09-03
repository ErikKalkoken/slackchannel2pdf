from pathlib import Path

from slackchannel2pdf.fpdf_extension import FPDFext


def main():
    html = """You can now easily print text mixing different styles: <b>bold</b>, <i>italic</i>, <u>underlined</u>, or <b><i><u>all at once</u></i></b>!<br><br>You can also insert links on text, such as <a href="http://www.fpdf.org" blank="_target">www.fpdf.org</a>, or this <s fontfamily="Courier" size="20" style="U">some custom text </s> - yeah!"""  # noqa

    document = FPDFext()
    document.add_page()
    document.set_font("Arial", size=12)
    document.cell(w=0, txt="hello world")
    document.write_html(5, html)

    document.ln()
    document.ln()

    html = (
        "This is some normal text<br><blockquote>This is more text</blockquote>"
        "And this is the final text"
    )
    document.write_html(5, html)

    path = Path(__file__) / "test_fpdf_ext.pdf"
    document.output(str(path))


if __name__ == "__main__":
    main()
