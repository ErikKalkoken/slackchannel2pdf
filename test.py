from fpdf import FPDF

# create PDF
document = FPDF()
document.add_page()
document.set_font('Arial', size=12)
document.write(5,"Hello world\n")
document.write(5,"Hello again\n")
document.output("hello_world.pdf")
