# example script for fetching the history of a conversation
# result will be written to file as JSON array

import os
import slack
import re
import fpdf
from config import *
from my_slack import *
from fpdf_ext import FPDF_ext
from datetime import datetime

class Exporter:
    
    def __init__(self, user_names, channel_names):
        self.user_names = user_names
        self.channel_names = channel_names


    def _transform_text(self, text):    
        """ remove characters from text that can not be displayed in the PDF """
        text2 = text.encode('latin-1', 'replace').decode('latin-1')
        return text2


    def _replace_markup_in_text(self, matchObj):
    
            match = matchObj.group(1)

            id_chars = match[0:2]
            id_raw = match[1:len(match)]
            parts = id_raw.split("|", 1)
            id = parts[0]

            if id_chars == "@U" or id_chars == "@W":
                # match is a user ID
                if id in self.user_names:
                    replacement = "@" + self.user_names[id]
                else:
                    replacement = "@[unknown user:{}]".format(id)
            
            elif id_chars == "#C":
                # match is a channel ID
                if id in self.channel_names:
                    replacement = "#" + self.channel_names[id]
                else:
                    replacement = "#[unknown channel:{}]".format(id)
            
            elif match[0:9] == "!subteam":
                # match is a user group ID
                replacement = "[user group]"
            
            elif match[0:1] == "!":
                # match is a special mention
                if id == "here":
                    replacement = "@here"
                
                elif id == "channel":
                    replacement = "@channel"
                
                elif id == "everyone":
                    replacement = "@everyone"                    
            
                elif match[0:5] == "!date":
                    date_parts = match.split("^")
                    if len(date_parts) > 1:
                        replacement = self.get_datetime_formatted_str(date_parts[1])
                    else:
                        replacement = "(failed to parse date)"

                else:
                    replacement = "[unknown: {}]". format(id)
            
            else:
                # match is an URL
                link_parts = match.split("|")
                if len(link_parts) == 2:
                    replacement = '<a href="' + link_parts[0] + '">' + link_parts[1] + '</a>'
                else:
                    replacement = "(unknown)"
            
            return replacement


    def _transform_markup_text(self, text):    
        """ 
        remove unsupported characters and resolve formatting, e.g. <!here> 
        """
        # pass 1 - adjust encoding
        s = self._transform_text(text)

        # pass 2 - transform markups with brackets
        s2 = re.sub(
            r'<(.*?)>',
            self._replace_markup_in_text,
            text
        )

        # pass 3 - transform formatting markups

        # bold
        s2 = re.sub(
            r'[*]([^*]+)[*]',
            r'<b>\1</b>',
            s2
        )

        # code
        s2 = re.sub(
            r'[`]([^`]+)[`]',
            r'<s fontfamily="Courier">\1</s>',
            s2
        )

        return s2
        

    def get_datetime_formatted_str(self, ts):
        """ return given timestamp as formated datetime string """
        return datetime.utcfromtimestamp(round(float(ts))).strftime('%Y-%m-%d %H:%M:%S')

    def _parse_test_and_write(self, document, line_height, html):
        document.write_html(line_height, html)

    def parse_message_and_write_pdf(self, document, msg, margin_left, last_user_id):
        """ parse message to write and add to PDF """
        
        if "user" in msg:
            user_id = msg["user"]
            if user_id in self.user_names:
                user_name = self.user_names[user_id]
            else:
                user_name = "[unknown user]"
        
        elif "bot_id" in msg:
            user_id = msg["bot_id"]
            if "username" in msg:
                user_name = msg["username"]
            else:
                user_name = "[unknown bot]"
        else:
            user_name = None
            
        if user_name is not None: 
            # start again on the left border        
            document.set_left_margin(margin_left)
            document.set_x(margin_left)
            
            if last_user_id != user_id:
                # write user name and date only when user switches
                document.ln()
                document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL, style="B")
                document.write(LINE_HEIGHT_DEFAULT, user_name + " ")
                
                datetime_str = self.get_datetime_formatted_str(msg["ts"])
                document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_SMALL)
                document.write(LINE_HEIGHT_DEFAULT, datetime_str)
                document.ln()            
            
            if "text" in msg:
                document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL)            
                self._parse_test_and_write(document, LINE_HEIGHT_DEFAULT, self._transform_markup_text(msg["text"]))
                document.ln()

            if "attachments" in msg:
                document.ln()
                document.set_left_margin(margin_left + TAB_INDENT)
                document.set_x(margin_left + TAB_INDENT)
                
                for attach in msg["attachments"]:            
                    if "pretext" in attach:
                        document.set_left_margin(margin_left)
                        document.set_x(margin_left)
                        document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL)
                        document.write(LINE_HEIGHT_DEFAULT, self._transform_markup_text(attach["pretext"]))
                        document.set_left_margin(margin_left + TAB_INDENT)
                        document.set_x(margin_left + TAB_INDENT)
                        document.ln()

                    if "author_name" in attach:
                        document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_LARGE, style="B")
                        document.write(LINE_HEIGHT_DEFAULT, self._transform_text(attach["author_name"]))
                        document.ln()

                    if "title" in attach:
                        document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL, style="B")
                        document.write(LINE_HEIGHT_DEFAULT, self._transform_text(attach["title"]))
                        document.ln()
                    
                    if "text" in attach:
                        document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL)
                        document.write(LINE_HEIGHT_DEFAULT, self._transform_markup_text(attach["text"]))
                        document.ln()

                    if "fields" in attach:
                        for field in attach["fields"]:
                            document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL, style="B")
                            document.write(LINE_HEIGHT_DEFAULT, self._transform_text(field["title"]))
                            document.ln()
                            document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL)
                            document.write(LINE_HEIGHT_DEFAULT, self._transform_markup_text(field["value"]))
                            document.ln()

                    
                    if "footer" in attach:                
                        if "ts" in attach:
                            text = "{} | {}".format(
                                self._transform_text(attach["footer"]), 
                                self.get_datetime_formatted_str(attach["ts"])
                            )
                        else:
                            text = self._transform_text(attach["footer"])

                        document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_SMALL)
                        document.write(LINE_HEIGHT_DEFAULT, text)
                        document.ln()

                    if "image_url" in attach:
                        document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL)
                        document.write(LINE_HEIGHT_DEFAULT, "[Image]")
                        document.ln()

                    document.ln()
        else:
            user_id = None

        return user_id   


def draw_line_for_threads(document):    
    x0 = MARGIN_LEFT + TAB_INDENT
    x1 = x0 + 20
    y = document.get_y() + 3
    document.line(x0, y, x1, y)


def main():    
    CHANNEL = "G7LULJD46"

    # fetch data from Slack
    client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
    workspace_info = client.auth_test()
    assert workspace_info["ok"]
    filename = workspace_info["team_id"] + "_" + CHANNEL

    user_names = fetch_user_names(client)
    channel_names = fetch_channel_names(client)

    messages = fetch_messages_for_channel(client, CHANNEL, 500)
    threads = fetch_threads_for_messages(client, CHANNEL, messages)
    write_messages_to_file(messages, filename)
    write_messages_to_file(threads, filename + "_threads")

    # create PDF
    document = FPDF_ext()
    document.add_page()

    exporter = Exporter(user_names, channel_names)

    # write title
    title = "Slack Workspace: {} / Channel: {}".format(
        workspace_info["team"],
        channel_names[CHANNEL]
    )
    document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_LARGE, style="B")
    document.set_left_margin(MARGIN_LEFT)
    document.set_x(MARGIN_LEFT)
    document.write(LINE_HEIGHT_DEFAULT, title)
    document.ln()

    last_user_id = None
    latest_date = None
    for msg in reversed(messages):
        
        # write day seperator if needed
        msg_date = datetime.utcfromtimestamp(round(float(msg["ts"]))).date()    
        if msg_date != latest_date:
            document.ln()
            document.ln()
            document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL, style="U")
            document.set_left_margin(MARGIN_LEFT)
            document.set_x(MARGIN_LEFT)
            document.write(LINE_HEIGHT_DEFAULT, msg_date.strftime('%Y-%m-%d'))        
            document.ln()
            latest_date = msg_date
        
        last_user_id = exporter.parse_message_and_write_pdf(
            document, 
            msg, 
            MARGIN_LEFT, 
            last_user_id
        )
        if "thread_ts" in msg and msg["thread_ts"] == msg["ts"]:
            thread_ts = msg["thread_ts"]
            
            if thread_ts in threads:
                draw_line_for_threads(document)

                for thread_msg in reversed(threads[thread_ts]):
                    last_user_id = exporter.parse_message_and_write_pdf(
                        document, 
                        thread_msg, 
                        MARGIN_LEFT + TAB_INDENT, 
                        last_user_id
                    )
                
                draw_line_for_threads(document)
            
            last_user_id = None
            
    # store PDF
    filenamePdf = filename + ".pdf"
    print("Writing messages as PDF to file: " + filenamePdf)
    document.output(filenamePdf)

if __name__ == '__main__':
    main()
