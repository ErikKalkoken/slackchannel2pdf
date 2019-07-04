import unittest
from run import Exporter

class TestExporter(unittest.TestCase):

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

        self.exporter = Exporter(user_names, channel_names)


    def test_transform_markup_text(self):
        self.assertEqual(
            self.exporter._transform_markup_text("<@U623456789>"), 
            '@Janet'
        )
        self.assertEqual(
            self.exporter._transform_markup_text("<#C723456789>"), 
            '#tokio'
        )
        self.assertEqual(
            self.exporter._transform_markup_text("<!everyone>"), 
            '@everyone'
        )        
        self.assertEqual(
            self.exporter._transform_markup_text("<!here>"), 
            '@here'
        )
        self.assertEqual(
            self.exporter._transform_markup_text("<!channel>"), 
            '@channel'
        )
        self.assertEqual(
            self.exporter._transform_markup_text(
                "<!date^1392734382^Posted {date_num} {time_secs}|Posted 2014-02-18 6:39:42 AM PST>"
            ), 
            self.exporter.get_datetime_formatted_str(1392734382)
        )
        self.assertEqual(
            self.exporter._transform_markup_text("<https://www.google.com|Google>"), 
            '<a href="https://www.google.com">Google</a>'            
        )
        self.assertEqual(
            self.exporter._transform_markup_text("some text <@U623456789> more text"), 
            'some text @Janet more text'
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
            self.exporter._transform_markup_text("some *text <@U623456789>* more text"), 
            'some <b>text @Janet</b> more text'
        )

if __name__ == '__main__':
    unittest.main()