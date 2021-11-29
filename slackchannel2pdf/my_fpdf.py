from . import settings
from .fpdf_ext import FPDF_ext


class MyFPDF(FPDF_ext):
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
