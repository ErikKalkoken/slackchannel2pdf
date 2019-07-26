import unittest
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir + "/channelexport")
from channelexport import *


class TestExporterTransformText(unittest.TestCase):

    def setUp(self):
        user_names = {
            "U12345678": "Naoko",
            "U62345678": "Janet",
            "U72345678": "Yuna"
        }

        channel_names = {
            "C12345678": "berlin",
            "C72345678": "tokio",
            "C42345678": "oslo"
        }

        usergroup_names = {
            "S12345678": "admins",
            "S72345678": "marketing",
            "S42345678": "sales"
        }

        self.exporter = ChannelExporter("TEST")
        self.exporter._user_names = user_names
        self.exporter._channel_names = channel_names
        self.exporter._usergroup_names = usergroup_names

    
    def test_transform_encoding(self):
        self.assertEqual(
            self.exporter._transform_encoding("special char ✓"), 
            "special char ✓"
        )
        self.assertEqual(
            self.exporter._transform_encoding("&lt;"), 
            "<"
        )
        self.assertEqual(
            self.exporter._transform_encoding("&#60;"), 
            "<"
        )

    def test_transform_text_user(self):
        self.assertEqual(
            self.exporter._transform_text("<@U62345678>", True), 
            '<b>@Janet</b>'
        )
        self.assertEqual(
            self.exporter._transform_text("<@U999999999>", True), 
            '<b>@user_U999999999</b>'
        )
        self.assertEqual(
            self.exporter._transform_text("<@W999999999>", True), 
            '<b>@user_W999999999</b>'
        )
    
    def test_transform_text_channel(self):        
        self.assertEqual(
            self.exporter._transform_text("<#C72345678>", True), 
            '<b>#tokio</b>'
        )
        self.assertEqual(
            self.exporter._transform_text("<#C55555555>", True), 
            '<b>#channel_C55555555</b>'
        )
    
    def test_transform_text_usergroup(self):
        self.assertEqual(
            self.exporter._transform_text("<!subteam^S72345678>", True), 
            '<b>@marketing</b>'
        )

        self.assertEqual(
            self.exporter._transform_text("<!subteam^SAZ94GDB8>", True), 
            '<b>@usergroup_SAZ94GDB8</b>'
        )

    def test_transform_text_special(self):
        self.assertEqual(
            self.exporter._transform_text("<!everyone>", True), 
            '<b>@everyone</b>'
        )        
        self.assertEqual(
            self.exporter._transform_text("<!here>", True), 
            '<b>@here</b>'
        )
        self.assertEqual(
            self.exporter._transform_text("<!channel>", True), 
            '<b>@channel</b>'
        )
        self.assertEqual(
            self.exporter._transform_text(
                "<!date^1392734382^Posted {date_num} {time_secs}|Posted 2014-02-18 6:39:42 AM PST>", 
                True
            ), 
            self.exporter._get_datetime_formatted_str(1392734382)
        )
        self.assertEqual(
            self.exporter._transform_text("<!xyz>", True), 
            '<b>@special_xyz</b>'
        )
        
    def test_transform_text_url(self):
        self.assertEqual(
            self.exporter._transform_text(
                "<https://www.google.com|Google>", 
                True
                ), 
            '<a href="https://www.google.com">Google</a>'            
        )
        self.assertEqual(
            self.exporter._transform_text(
                "<https://www.google.com>", 
                True
                ), 
            '<a href="https://www.google.com">https://www.google.com</a>'
        )
    
    def test_transform_text_formatting(self):        
        self.assertEqual(
            self.exporter._transform_text("*bold*", True), 
            '<b>bold</b>'
        )
        self.assertEqual(
            self.exporter._transform_text("_italic_", True), 
            '<i>italic</i>'
        )
        self.assertEqual(
            self.exporter._transform_text(
                "text *bold* text _italic_ text", 
                True
                ), 
            'text <b>bold</b> text <i>italic</i> text'
        )
        self.assertEqual(
            self.exporter._transform_text("`code`", True), 
            '<s fontfamily="NotoSansMono">code</s>'
        )
        self.assertEqual(
            self.exporter._transform_text("*_bold+italic_*", True), 
            '<b><i>bold+italic</i></b>'
        )
        
    def test_transform_text_general(self):
        self.assertEqual(
            self.exporter._transform_text(
                "some *text* <@U62345678> more text", 
                True
                ), 
            'some <b>text</b> <b>@Janet</b> more text'
        )
        self.assertEqual(
            self.exporter._transform_text("first\nsecond\nthird", True), 
            'first<br>second<br>third'
        )
        
        self.assertEqual(
            self.exporter._transform_text(
                "some text <@U62345678> more text", 
                True
                ), 
            'some text <b>@Janet</b> more text'
        )

        self.assertEqual(
            self.exporter._transform_text(
                "before ident\n>indented text\nafter ident", 
                    True
                ), 
            'before ident<br><blockquote>indented text</blockquote><br>after ident'
        )

    


class TestExporterReduceToDict(unittest.TestCase):
    
    def setUp(self):
        self.a = [
            {
                "id": "1",
                "name_1": "Naoko Kobayashi",
                "name_2": "naoko.kobayashi"
            },
            {
                "id": "2",
                "name_1": "Janet Hakuli",
                "name_2": "janet.hakuli"
            },
            {
                "id": "3",                
                "name_2": "rosie.dunbar"
            },
            {
                "id": "4"
            },            
            {
                "name_1": "John Doe",
                "name_2": "john.doe"
            }

        ]
        self.exporter = ChannelExporter("TEST")

    def test_1(self):        
        expected = {
            "1": "Naoko Kobayashi",
            "2": "Janet Hakuli"
        }
        result = reduce_to_dict(
                self.a,
                "id",
                "name_1"
            )
        self.assertEqual(
            result, 
            expected
        )

    def test_2(self):        
        expected = {
            "1": "Naoko Kobayashi",
            "2": "Janet Hakuli",
            "3": "rosie.dunbar"
        }
        result = reduce_to_dict(
                self.a,
                "id",
                "name_1",
                "name_2"
            )
        self.assertEqual(
            result, 
            expected
        )

    def test_3(self):        
        expected = {
            "1": "naoko.kobayashi",
            "2": "janet.hakuli",
            "3": "rosie.dunbar"
        }
        result = reduce_to_dict(
                self.a,
                "id",
                "invalid_col",
                "name_2"
            )
        self.assertEqual(
            result, 
            expected
        )
    
if __name__ == '__main__':
    unittest.main()