import unittest
import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir + "/channelexport")
from channelexport import *
import PyPDF2
from datetime import datetime
from dateutil import parser
import pytz
from tzlocal import get_localzone
import babel

class TestExporterTransformText(unittest.TestCase):

    def setUp(self):
        workspace_info = {
            "team": "test",
            "user_id": "U9234567X"
        }
        user_names = {
            "U12345678": "Naoko Kobayashi",
            "U62345678": "Janet Hakuli",
            "U72345678": "Yuna Kobayashi",
            "U9234567X": "Erik Kalkoken",
            "U92345678": "Rosie Dunbar"
        }

        channel_names = {
            "C12345678": "berlin",
            "C72345678": "tokio",
            "C42345678": "oslo",
            "G1234567X": "channel-exporter",
            "G2234567X": "channel-exporter-2"
        }

        usergroup_names = {
            "S12345678": "admins",
            "S72345678": "marketing",
            "S42345678": "sales"
        }
        
        self.exporter = SlackChannelExporter("TEST")
        self.exporter._workspace_info = workspace_info
        self.exporter._user_names = user_names
        self.exporter._channel_names = channel_names
        self.exporter._usergroup_names = usergroup_names
        self.exporter._author = "Erik Kalkoken"


    def test_run_with_defaults(self):
        channels = ["G1234567X", "G2234567X"]        
        response = self.exporter.run(
            channels, 
            currentdir
        )        
        self.assertTrue(response["ok"])
        self.assertIn("G1234567X", response["channels"])
        self.assertIn("G2234567X", response["channels"])

        for channel_id in ["G1234567X", "G2234567X"]:            
            res_channel = response["channels"][channel_id]
            channel_name = self.exporter._channel_names[channel_id]
            self.assertEqual(
                res_channel["filename_pdf"], 
                os.path.join(
                    currentdir, 
                    (
                        self.exporter._workspace_info["team"]
                        + "_"
                        + channel_name
                        + ".pdf")
            ))
            self.assertTrue(os.path.isfile(res_channel["filename_pdf"]))

            # assert export details are correct
            self.assertTrue(res_channel["ok"])                        
            self.assertEqual(res_channel["dest_path"], currentdir)
            self.assertEqual(res_channel["page_format"], "a4")
            self.assertEqual(
                res_channel["page_orientation"], 
                "portrait"
            )
            self.assertEqual(
                res_channel["max_messages"], 
                SlackChannelExporter._MAX_MESSAGES_PER_CHANNEL
            )
            self.assertEqual(
                res_channel["timezone"], 
                get_localzone()
            )
            self.assertEqual(
                res_channel["locale"], 
                babel.Locale.default()
            )
            
            # assert infos in PDF file are correct
            pdf_file = open(res_channel["filename_pdf"], 'rb') 
            pdf_reader = PyPDF2.PdfFileReader(pdf_file)
            doc_info = pdf_reader.getDocumentInfo()
            self.assertEqual(doc_info.author, "Erik Kalkoken")
            self.assertEqual(
                doc_info.creator, 
                "Channel Export v" + SlackChannelExporter._VERSION
            )
            self.assertEqual(
                doc_info.title, 
                (self.exporter._workspace_info["team"] 
                    + " / " + channel_name)
            )
            

    def test_run_with_args_1(self):
        # self.exporter._channel_names["G2234567X"] = "channel-exporter-run_with_args_1"
        response = self.exporter.run(
            ["G2234567X"], 
            currentdir,
            None,
            None,
            "landscape",
            "a3",
            42
        )        
        self.assertTrue(response["ok"])
        self.assertIn("G2234567X", response["channels"])
        res_channel = response["channels"]["G2234567X"]

        # assert export details are correct
        self.assertTrue(res_channel["ok"])
        self.assertEqual(res_channel["message_count"], 4)
        self.assertEqual(res_channel["thread_count"], 0)
        self.assertEqual(res_channel["dest_path"], currentdir)
        self.assertEqual(res_channel["page_format"], "a3")
        self.assertEqual(res_channel["page_orientation"], "landscape")
        self.assertEqual(
            res_channel["max_messages"], 
            42
        )
           

    """
    def test_run_with_error(self):
        self.assertRaises(RuntimeError, self.exporter.run(
            ["channel-exporter"], 
            "invalid_path"
        ))        
    """
        

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
            '<b>@Janet Hakuli</b>'
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
            'some <b>text</b> <b>@Janet Hakuli</b> more text'
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
            'some text <b>@Janet Hakuli</b> more text'
        )

        self.assertEqual(
            self.exporter._transform_text(
                "before ident\n>indented text\nafter ident", 
                    True
                ), 
            'before ident<br><blockquote>indented text</blockquote><br>after ident'
        )

    
class TestExporterTimezonesNLocale(unittest.TestCase):

    def setUp(self):
        workspace_info = {
            "team": "test",
            "user_id": "U9234567X"
        }
        user_names = {
            "U12345678": "Naoko Kobayashi",
            "U62345678": "Janet Hakuli",
            "U72345678": "Yuna Kobayashi",
            "U9234567X": "Erik Kalkoken",
        }

        channel_names = {
            "C12345678": "berlin",
            "C72345678": "tokio",
            "C42345678": "oslo",
            "G1234567X": "channel-exporter",
            "G2234567X": "channel-exporter-2"
        }

        usergroup_names = {
            "S12345678": "admins",
            "S72345678": "marketing",
            "S42345678": "sales"
        }
        
        self.exporter = SlackChannelExporter(
            "TEST",
            pytz.timezone('Asia/Bangkok'),
            babel.Locale.parse("es-MX", sep='-')
        )
        self.exporter._workspace_info = workspace_info
        self.exporter._user_names = user_names
        self.exporter._channel_names = channel_names
        self.exporter._usergroup_names = usergroup_names

    
    def test_timezone_locale(self):
        #self.exporter._channel_names["G2234567X"] = "channel-exporter-timezone-locale"
        channels = ["G2234567X"]
        response = self.exporter.run(
            channels, 
            currentdir
        )        
        self.assertTrue(response["ok"])
        res_channel = response["channels"]["G2234567X"]

        # assert export details are correct
        self.assertTrue(res_channel["ok"])
        self.assertEqual(
            res_channel["timezone"], 
            pytz.timezone('Asia/Bangkok'),
        )
        self.assertEqual(
            res_channel["locale"], 
            babel.Locale.parse("es-MX", sep='-')
        )

    def test_get_datetime(self):
        ts = 1006300923
        dt = self.exporter._get_datetime_from_ts(ts)
        self.assertEqual(
            dt.timestamp(),
            ts
        )

    def test_dummy(self):
        dt = datetime.utcnow()
        print(self.exporter._format_datetime_str(dt))
        print(self.exporter._get_datetime_formatted_str(dt.timestamp()))
                

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
        self.exporter = SlackChannelExporter("TEST")

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

"""
class TestExporterSlackMethods(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.exporter = SlackChannelExporter(os.environ['SLACK_TOKEN'])

    def test_fetch_messages(self):
        oldest = parser.parse("2019-JUL-04")
        oldest = self.exporter._tz_local.localize(oldest)

        latest = parser.parse("2019-JUL-06")
        latest = self.exporter._tz_local.localize(latest)
                
        messages = self.exporter._fetch_messages_from_channel(
            channel_id="G7LULJD46",
            max_messages=1000
        )
        self.assertIsInstance(messages, list)

        messages = self.exporter._fetch_messages_from_channel(
            channel_id="G7LULJD46",
            max_messages=1000,
            oldest=oldest,
            latest=latest
        )
        self.assertIsInstance(messages, list)
"""    

    
if __name__ == '__main__':
    unittest.main()    
    
    """
    singletest = unittest.TestSuite()
    singletest.addTest(TestExporterTimezonesNLocale("test_dummy"))
    unittest.TextTestRunner().run(singletest)    
    """
    