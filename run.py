# example script for fetching the history of a conversation
# result will be written to file as JSON array

import os
import slack
import re
import fpdf
from config import *
from my_slack import *
from fpdf import FPDF
from datetime import datetime


def transform_text(text):    
    """ remove characters from text that can not be displayed in the PDF """
    text2 = text.encode('latin-1', 'replace').decode('latin-1')
    return text2


def transform_formatted_text(text):    
    """ remove unsupported characters and resolve formatting, e.g. <!here> """
    
    s = transform_text(text)
    pattern = re.compile(r'<(.*?)>')

    while True:
        m = pattern.search(s)    
        if m is not None:
            match = m.group(1)
            id_chars = match[0:2]
            id_raw = match[1:len(match)]
            parts = id_raw.split("|", 1)
            id = parts[0]

            if id_chars == "@U" or id_chars == "@W":
                # match is a user ID
                if id in user_names:
                    name = "@" + user_names[id]
                else:
                    name = "@[unknown user:{}]".format(id)
            
            elif id_chars == "#C":
                # match is a channel ID
                if id in channel_names:
                    name = "#" + channel_names[id]
                else:
                    name = "#[unknown channel:{}]".format(id)
            
            elif match[0:9] == "!subteam":
                # match is a user group ID
                name = "[user group]"
            
            elif match[0:1] == "!":
                # match is a special mention
                if id == "here":
                    name = "@here"
                elif id == "channel":
                    name = "@channel"
                elif id == "everyone":
                    name = "@everyone"
                elif id == "date":
                    if len(parts) == 2:
                        name = parts[1]
                    else:
                        name = "(failed to parse date)"
                else:
                    name = "[unknown: {}]". format(id)

            else:
                # match is an URL
                if len(parts) == 2:
                    name = parts[1]
                else:
                    name = "(unknown)"

            # replace the match with the found name in the string
            start = m.span()[0]
            end = m.span()[1]
            s = s[0:start] + name + s[end:len(s)]
        else:
            break

    return s


def get_datetime_formatted_str(ts):
    """ return given timestamp as formated datetime string """
    return datetime.utcfromtimestamp(round(float(ts))).strftime('%Y-%m-%d %H:%M:%S')

def parse_markup_and_write(document, line_height, text):    
    document.write(line_height, text)

def parse_message_and_write_pdf(document, msg, margin_left, last_user_id):
    """ parse message to write and add to PDF """
    
    if "user" in msg:
        user_id = msg["user"]
        if user_id in user_names:
            user_name = user_names[user_id]
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
            
            datetime_str = get_datetime_formatted_str(msg["ts"])
            document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_SMALL)
            document.write(LINE_HEIGHT_DEFAULT, datetime_str)
            document.ln()            
        
        if "text" in msg:
            document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL)            
            parse_markup_and_write(document, LINE_HEIGHT_DEFAULT, transform_formatted_text(msg["text"]))
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
                    document.write(LINE_HEIGHT_DEFAULT, transform_formatted_text(attach["pretext"]))
                    document.set_left_margin(margin_left + TAB_INDENT)
                    document.set_x(margin_left + TAB_INDENT)
                    document.ln()

                if "author_name" in attach:
                    document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_LARGE, style="B")
                    document.write(LINE_HEIGHT_DEFAULT, transform_text(attach["author_name"]))
                    document.ln()

                if "title" in attach:
                    document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL, style="B")
                    document.write(LINE_HEIGHT_DEFAULT, transform_text(attach["title"]))
                    document.ln()
                
                if "text" in attach:
                    document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL)
                    document.write(LINE_HEIGHT_DEFAULT, transform_formatted_text(attach["text"]))
                    document.ln()

                if "fields" in attach:
                    for field in attach["fields"]:
                        document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL, style="B")
                        document.write(LINE_HEIGHT_DEFAULT, transform_text(field["title"]))
                        document.ln()
                        document.set_font(FONT_FAMILY_DEFAULT, size=FONT_SIZE_NORMAL)
                        document.write(LINE_HEIGHT_DEFAULT, transform_formatted_text(field["value"]))
                        document.ln()

                
                if "footer" in attach:                
                    if "ts" in attach:
                        text = "{} | {}".format(
                            transform_text(attach["footer"]), 
                            get_datetime_formatted_str(attach["ts"])
                        )
                    else:
                        text = transform_text(attach["footer"])

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


def draw_line_for_threads():    
    x0 = MARGIN_LEFT + TAB_INDENT
    x1 = x0 + 20
    y = document.get_y() + 3
    document.line(x0, y, x1, y)


# main
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
document = FPDF()
document.add_page()

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
    
    last_user_id = parse_message_and_write_pdf(
        document, 
        msg, 
        MARGIN_LEFT, 
        last_user_id
    )
    if "thread_ts" in msg and msg["thread_ts"] == msg["ts"]:
        thread_ts = msg["thread_ts"]
        
        if thread_ts in threads:
            draw_line_for_threads()

            for thread_msg in reversed(threads[thread_ts]):
                last_user_id = parse_message_and_write_pdf(
                    document, 
                    thread_msg, 
                    MARGIN_LEFT + TAB_INDENT, 
                    last_user_id
                )
            
            draw_line_for_threads()
        
        last_user_id = None
        
# store PDF
filenamePdf = filename + ".pdf"
print("Writing messages as PDF to file: " + filenamePdf)
document.output(filenamePdf)

