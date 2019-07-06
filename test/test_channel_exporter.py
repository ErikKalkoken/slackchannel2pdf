import unittest
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
from channel_exporter import ChannelExporter

class TestExporterTransformations(unittest.TestCase):

    def setUp(self):
        user_names = {
            "U123456789": "Naoko",
            "U623456789": "Janet",
            "U723456789": "Yuna"
        }

        channel_names = {
            "C123456789": "berlin",
            "C723456789": "tokio",
            "C423456789": "oslo"
        }

        self.exporter = ChannelExporter("TEST")
        self.exporter._user_names = user_names
        self.exporter._channel_names = channel_names


    def test_transform_text(self):
        self.assertEqual(
            self.exporter._transform_markup_text("special char ✓"), 
            "special char ?"
        )
        self.assertEqual(
            self.exporter._transform_markup_text("&lt;"), 
            "<"
        )
        self.assertEqual(
            self.exporter._transform_markup_text("&#60;"), 
            "<"
        )
    
    def test_transform_markup_text(self):
        self.assertEqual(
            self.exporter._transform_markup_text("<@U623456789>"), 
            '<b>@Janet</b>'
        )
        self.assertEqual(
            self.exporter._transform_markup_text("<@U999999999>"), 
            '<b>@unknown_U999999999</b>'
        )
        self.assertEqual(
            self.exporter._transform_markup_text("<#C723456789>"), 
            '<b>#tokio</b>'
        )
        self.assertEqual(
            self.exporter._transform_markup_text("<!everyone>"), 
            '<b>@everyone</b>'
        )        
        self.assertEqual(
            self.exporter._transform_markup_text("<!here>"), 
            '<b>@here</b>'
        )
        self.assertEqual(
            self.exporter._transform_markup_text("<!channel>"), 
            '<b>@channel</b>'
        )
        self.assertEqual(
            self.exporter._transform_markup_text(
                "<!date^1392734382^Posted {date_num} {time_secs}|Posted 2014-02-18 6:39:42 AM PST>"
            ), 
            self.exporter._get_datetime_formatted_str(1392734382)
        )
        self.assertEqual(
            self.exporter._transform_markup_text("<https://www.google.com|Google>"), 
            '<a href="https://www.google.com">Google</a>'            
        )
        self.assertEqual(
            self.exporter._transform_markup_text("<https://www.google.com>"), 
            '<a href="https://www.google.com">https://www.google.com</a>'
        )
        self.assertEqual(
            self.exporter._transform_markup_text("some text <@U623456789> more text"), 
            'some text <b>@Janet</b> more text'
        )
        self.assertEqual(
            self.exporter._transform_markup_text("*bold*"), 
            '<b>bold</b>'
        )
        self.assertEqual(
            self.exporter._transform_markup_text("`code`"), 
            '<s fontfamily="Courier">code</s>'
        )
        self.assertEqual(
            self.exporter._transform_markup_text("some *text* <@U623456789> more text"), 
            'some <b>text</b> <b>@Janet</b> more text'
        )
        self.assertEqual(
            self.exporter._transform_markup_text("first\nsecond\nthird"), 
            'first<br>second<br>third'
        )
        self.assertEqual(
            self.exporter._transform_markup_text("<!subteam>"), 
            '<b>@usergroup_dummy</b>'
        )        
        self.assertEqual(
            self.exporter._transform_markup_text("before ident\n>indented text\nafter ident"), 
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
        result = self.exporter._reduce_to_dict(
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
        result = self.exporter._reduce_to_dict(
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
        result = self.exporter._reduce_to_dict(
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