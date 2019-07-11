from fpdf_ext import FPDF_ext

document = FPDF_ext()

document.add_font("NotoSans", style="", fname="NotoSans-Regular.ttf", uni=True)
document.add_font("NotoEmoji", style="", fname="NotoEmoji-Regular.ttf", uni=True)

document.add_page()
document.set_font('NotoSans', size=12)
document.write(5, "hello world. how’s everyone doing?")
document.ln()
document.ln()
document.set_font('NotoEmoji', size=12)
document.write(5, u"\U0001F436")
document.ln()
document.output("emoji.pdf")
