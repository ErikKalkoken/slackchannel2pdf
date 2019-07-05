import re
import html
import json
import os
from time import sleep
from datetime import datetime
from time import sleep
import slack
import fpdf
from fpdf_ext import FPDF_ext


class ChannelExporter:
    """Class for exporting slack channels to PDF files

    This class will fetch all messages including threads from a Slack
    channel and then export them into a PDF file.

    The export will only include the text content, but not any media
    content like icons, images, etc. Media content is represented by 
    placeholders with hyperlinks.

    Active elements of Slack message like buttons, menus, etc. 
    are represented by placeholders.

    Emojis are included with their textual representation.

    Names of users, bots and channels are automatically resolved if possible.

    Attachments and blocks are supported.

    """    
    # style and layout settings for PDF
    _FONT_FAMILY_DEFAULT = "Arial"
    _FONT_SIZE_NORMAL = 12
    _FONT_SIZE_LARGE = 14
    _FONT_SIZE_SMALL = 10
    _LINE_HEIGHT_DEFAULT = 6
    _MARGIN_LEFT = 10
    _TAB_WIDTH = 4
    _FORMAT_DATETIME_SHORT = '%Y-%m-%d'
    _FORMAT_DATETIME_LONG = '%Y-%m-%d %H:%M:%S'

    # limits for fetching messages from Slack
    _MESSAGES_PER_PAGE = 200 # max message retrieved per request during paging
    _MAX_MESSAGES_PER_CHANNEL = 10000
    _MAX_MESSAGES_PER_THREAD = 500


    def __init__(self, slack_token):        
        """CONSTRUCTOR
        Slack token needs to be provided for init
        class will run in test mode if given a token called "TEST"
        """
        if slack_token != "TEST":
            self._client = slack.WebClient(token=slack_token)        
            self._workspace_info = self._fetch_workspace_info()
            self._user_names = self._fetch_user_names()
            self._channel_names = self._fetch_channel_names()

        else:
            # if started with TEST parameter class properties will be
            # initialized empty and need to be set manually in test setup
            self._client = None
            self._workspace_info = dict()
            self._user_names = dict()
            self._channel_names = dict()


    # *************************************************************************
    # Methods for fetching data from Slack API
    # *************************************************************************

    def _fetch_messages_from_channel(self, channel_id, max_messages=None):
        """retrieve messages from a channel on Slack and return as list"""
        
        if max_messages is None:
            max_messages = self._MAX_MESSAGES_PER_CHANNEL

        messages_per_page = min(self._MESSAGES_PER_PAGE, max_messages)
        # get first page
        page = 1
        print("Retrieving page {}".format(page))
        response = self._client.conversations_history(
            channel=channel_id,
            limit=messages_per_page,
        )
        assert response["ok"]
        messages_all = response['messages']

        # get additional pages if below max message and if they are any
        while (len(messages_all) < max_messages and 
                response['has_more']):
            page += 1
            print("Retrieving page {}".format(page))
            sleep(1)   # need to wait 1 sec before next call due to rate limits
            # allow smaller page sized to fetch final page
            page_limit = min(
                messages_per_page, 
                max_messages - len(messages_all))
            response = self._client.conversations_history(
                channel=channel_id,
                limit=page_limit,
                cursor=response['response_metadata']['next_cursor']
            )
            assert response["ok"]
            messages = response['messages']
            messages_all = messages_all + messages

        print("Fetched a total of {} messages from channel {}".format(
            len(messages_all),
            channel_id
            ))

        return messages_all


    def _read_messages_from_file(self, filename):
        """reads list of message from a json file and returns it
        
        used mainly for testing 
        """     
        filename += '.json'
        try:
            with open(filename, 'r') as f:
                messages = json.load(f)
            print("read {} message from file: name {}".format(
                len(messages),
                filename
                ))
        except:
            print("failed to read from {}".format(filename))
            messages = list()
        return messages


    def _write_messages_to_file(self, messages, filename='messages'):
        """writes list of message to a json file 

        used mainly for testing 
        """     
        filename += '.json' 
        with open(filename , 'w', encoding='utf-8') as f:
            json.dump(
                messages, 
                f, 
                sort_keys=True, 
                indent=4, 
                ensure_ascii=False
                )
        print("written message to file: name {}".format(filename))
    

    def _fetch_messages_from_thread(
        self, 
        channel_id, 
        thread_ts, 
        max_messages=None):
        """retrieve messages from a Slack thread and return as list"""
        
        if max_messages is None:
            max_messages = self._MAX_MESSAGES_PER_THREAD
        
        messages_per_page = min(self._MESSAGES_PER_PAGE, max_messages)
        # get first page
        page = 1
        print("Threads for message {} - retrieving page {}".format(
            thread_ts,
            page
            ))
        response = self._client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            limit=messages_per_page
        )
        assert response["ok"]
        messages_all = response['messages']

        # get additional pages if below max message and if they are any
        while (len(messages_all) + messages_per_page <= max_messages and 
                response['has_more']):
            page += 1
            print("Threads for message {} - retrieving page {}".format(
                thread_ts,
                page
                ))
            sleep(1)   # need to wait 1 sec before next call due to rate limits
            response = self._client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                limit=messages_per_page,
                cursor=response['response_metadata']['next_cursor']
            )
            assert response["ok"]
            messages = response['messages']
            messages_all = messages_all + messages

        print("Fetched a total of {} thread messages from message {}".format(
                len(messages_all),                
                thread_ts
            ))

        return messages_all


    def _fetch_threads_from_messages(
        self, 
        channel_id, 
        messages, 
        max_messages=None):
        """returns threads for all message from for a channel as dict"""
        
        if max_messages is None:
            max_messages = self._MAX_MESSAGES_PER_THREAD
        
        threads = dict()
        for msg in messages:
            if "thread_ts" in msg and msg["thread_ts"] == msg["ts"]:
                thread_ts = msg["thread_ts"]
                thread_messages = self._fetch_messages_from_thread(                    
                    channel_id, 
                    thread_ts,
                    max_messages
                )            
                threads[thread_ts] = thread_messages
        return threads


    def _reduce_to_dict(
        self, 
        arr, 
        key_name, 
        col_name_primary, 
        col_name_secondary=None):
        """returns dict with selected columns as key and value from list of dict
        
        Args:
            arr: list of dicts to reduce
            key_name: name of column to become key
            col_name_primary: colum will become value if it exists
            col_name_secondary: colum will become value if col_name_primary 
                does not exist and this argument is provided

        dict items with no matching key_name, col_name_primary and 
        col_name_secondary will not be included in the resulting new dict

        """
        arr2 = dict()
        for item in arr:
            if key_name in item:
                key = item[key_name]
                if col_name_primary in item:
                    arr2[key] = item[col_name_primary]
                elif (col_name_secondary is not None and 
                        col_name_secondary in item):
                    arr2[key] = item[col_name_secondary]            
        return arr2


    def _fetch_user_names(self):    
        """returns dict of user names with user ID as key"""
        response = self._client.users_list()
        assert response["ok"]    
        user_names = self._reduce_to_dict(
            response["members"], 
            "id", 
            "real_name", 
            "name"
            )
        return user_names    


    def _fetch_channel_names(self):
        """returns dict of channel names with channel ID as key"""
        response = self._client.conversations_list(
            types="public_channel,private_channel")
        assert response["ok"]    
        channel_names = self._reduce_to_dict(
            response["channels"], 
            "id", 
            "name"
            )
        return channel_names    


    def _fetch_workspace_info(self):    
        """returns dict with info about current workspace"""
        response = self._client.auth_test()
        assert response["ok"]
        return response


    # *************************************************************************
    # Methods for parsing and transforming Slack messages
    # *************************************************************************

    def _transform_text(self, text):    
        """return string where non latin-1 characters have been replaced"""
        text = html.unescape(text)
        text2 = text.encode('latin-1', 'replace').decode('latin-1')
        return text2


    def _transform_markup_text(self, text):    
        """transforms markup text into HTML text for PDF output
        
        Main method to resolve all markups, e.g. <C12345678>, <!here>, *bold*
        Will resolve channel and user IDs to their names if possible
        Returns string with rudimentary HTML for formatting and links
        """
        
        def replace_markup_in_text(matchObj):
            """inline function returns replacement string for re.sub            
            
            This function does the actual resolving of IDs and markup key words
            """             
            match = matchObj.group(1)

            id_chars = match[0:2]
            id_raw = match[1:len(match)]
            parts = id_raw.split("|", 1)
            id = parts[0]

            if id_chars == "@U" or id_chars == "@W":
                # match is a user ID
                if id in self._user_names:
                    replacement = "@" + self._user_names[id]
                else:
                    replacement = "@[unknown user:{}]".format(id)
            
            elif id_chars == "#C":
                # match is a channel ID
                if id in self._channel_names:
                    replacement = "#" + self._channel_names[id]
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
                        replacement = self._get_datetime_formatted_str(
                            date_parts[1]
                            )
                    else:
                        replacement = "(failed to parse date)"

                else:
                    replacement = "[unknown: {}]". format(id)
            
            else:
                # match is an URL
                link_parts = match.split("|")
                if len(link_parts) == 2:
                    replacement = ('<a href="' 
                        + link_parts[0] 
                        + '">' 
                        + link_parts[1] 
                        + '</a>')
                else:
                    replacement = "(unknown)"

            return replacement


        # pass 1 - adjust encoding and transform HTML entities
        s = self._transform_text(text)        

        # pass 2 - transform markups with brackets
        s2 = re.sub(
            r'<(.*?)>',
            replace_markup_in_text,
            s
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

        # idents
        s2 = re.sub(
            r'^>(.+)',
            r'<blockquote>\1</blockquote>',
            s2,
            0,
            re.MULTILINE
            )

        s2 = s2.replace("</blockquote><br>", "</blockquote>")

        # EOF
        s2 = s2.replace("\n", "<br>")

        
        return s2


    def _get_datetime_formatted_str(self, ts):
        """return given timestamp as formated datetime string"""
        return datetime.utcfromtimestamp(
            round(float(ts))).strftime(self._FORMAT_DATETIME_LONG)


    def _parse_test_and_write(self, document, line_height, html):
        document.write_html(line_height, html)


    def _parse_message_and_write_pdf(
            self, 
            document, 
            msg, 
            margin_left, 
            last_user_id):
        """parse message to write and add to PDF"""
        
        if "user" in msg:
            user_id = msg["user"]
            if user_id in self._user_names:
                user_name = self._user_names[user_id]
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
                document.set_font(
                    self._FONT_FAMILY_DEFAULT, 
                    size=self._FONT_SIZE_NORMAL, 
                    style="B")
                document.write(self._LINE_HEIGHT_DEFAULT, user_name + " ")
                
                datetime_str = self._get_datetime_formatted_str(msg["ts"])
                document.set_font(
                    self._FONT_FAMILY_DEFAULT, 
                    size=self._FONT_SIZE_SMALL)
                document.write(self._LINE_HEIGHT_DEFAULT, datetime_str)
                document.ln()            
            
            if "text" in msg:
                document.set_font(
                    self._FONT_FAMILY_DEFAULT, 
                    size=self._FONT_SIZE_NORMAL)            
                self._parse_test_and_write(
                    document, 
                    self._LINE_HEIGHT_DEFAULT, 
                    self._transform_markup_text(msg["text"]))
                document.ln()

            if "attachments" in msg:
                document.ln()
                document.set_left_margin(margin_left + self._TAB_WIDTH)
                document.set_x(margin_left + self._TAB_WIDTH)
                
                for attach in msg["attachments"]:            
                    if "pretext" in attach:
                        document.set_left_margin(margin_left)
                        document.set_x(margin_left)
                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, 
                            size=self._FONT_SIZE_NORMAL)
                        self._parse_test_and_write(
                            document, 
                            self._LINE_HEIGHT_DEFAULT, 
                            self._transform_markup_text(attach["pretext"]))
                        document.set_left_margin(
                            margin_left + self._TAB_WIDTH)
                        document.set_x(margin_left + self._TAB_WIDTH)
                        document.ln()

                    if "author_name" in attach:
                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, 
                            size=self._FONT_SIZE_LARGE, 
                            style="B")
                        document.write(
                            self._LINE_HEIGHT_DEFAULT, 
                            self._transform_text(attach["author_name"]))
                        document.ln()

                    if "title" in attach:
                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, 
                            size=self._FONT_SIZE_NORMAL, 
                            style="B")
                        document.write(
                            self._LINE_HEIGHT_DEFAULT, 
                            self._transform_text(attach["title"]))
                        document.ln()
                    
                    if "text" in attach:
                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, 
                            size=self._FONT_SIZE_NORMAL)
                        self._parse_test_and_write(
                            document, 
                            self._LINE_HEIGHT_DEFAULT, 
                            self._transform_markup_text(attach["text"]))
                        document.ln()

                    if "fields" in attach:
                        for field in attach["fields"]:
                            document.set_font(
                                self._FONT_FAMILY_DEFAULT, 
                                size=self._FONT_SIZE_NORMAL, 
                                style="B")
                            document.write(
                                self._LINE_HEIGHT_DEFAULT, 
                                self._transform_text(field["title"]))
                            document.ln()
                            document.set_font(
                                self._FONT_FAMILY_DEFAULT, 
                                size=self._FONT_SIZE_NORMAL)
                            document.write(
                                self._LINE_HEIGHT_DEFAULT, 
                                self._transform_markup_text(field["value"]))
                            document.ln()

                    
                    if "footer" in attach:                
                        if "ts" in attach:
                            text = "{} | {}".format(
                                self._transform_text(attach["footer"]), 
                                self._get_datetime_formatted_str(attach["ts"])
                            )
                        else:
                            text = self._transform_text(attach["footer"])

                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, 
                            size=self._FONT_SIZE_SMALL)
                        document.write(self._LINE_HEIGHT_DEFAULT, text)
                        document.ln()

                    if "image_url" in attach:
                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, 
                            size=self._FONT_SIZE_NORMAL)
                        document.write(self._LINE_HEIGHT_DEFAULT, "[Image]")
                        document.ln()

                    document.ln()
        else:
            user_id = None

        return user_id   


    def _draw_line_for_threads(self, document):
        """draw line on PDF document at current position to mark threads"""
        x0 = self._MARGIN_LEFT + self._TAB_WIDTH
        x1 = x0 + 20
        y = document.get_y() + 3
        document.line(x0, y, x1, y)


    def _generate_filename_base(self, channel_id):
        """returns base string for filename from team ID and channel ID"""
        return self._workspace_info["team_id"] + "_" + channel_id


    def run(self, channel_id, max_messages=None):
        """export all message from a channel and store them in a PDF
        
        Args:
            channel_id: ID of channel to retrieve messages from
            max_messages: maximum number of messages to retrieve (optional)
        """
        
        # fetch messages
        if self._client is not None:
            # if we have a client fetch data from Slack
            messages = self._fetch_messages_from_channel(channel_id, max_messages)
            threads = self._fetch_threads_from_messages(channel_id, messages)
            
            filename_base = self._generate_filename_base(channel_id)
            if os.environ['DEVELOPMENT_MODE'] == "true":
                # write raw messages and threads to file in development
                self._write_messages_to_file(messages, filename_base)
                self._write_messages_to_file(threads, filename_base + "_threads")
        else:
            # if we don't have a client we will try to fetch from a file
            # this is used for testing
            filename_base = "test/" + str(channel_id)
            messages = self._read_messages_from_file(filename_base)
            threads = self._read_messages_from_file(filename_base + "_threads")

        # create PDF
        document = FPDF_ext()
        document.add_page()

        # write title
        title = "Slack Workspace: {} / Channel: {}".format(
            self._workspace_info["team"],
            self._channel_names[channel_id]
        )
        document.set_font(
            self._FONT_FAMILY_DEFAULT, 
            size=self._FONT_SIZE_LARGE, 
            style="B"
            )
        document.set_left_margin(self._MARGIN_LEFT)
        document.set_x(self._MARGIN_LEFT)
        document.write(self._LINE_HEIGHT_DEFAULT, title)
        document.ln()

        last_user_id = None
        latest_date = None
        for msg in reversed(messages):
            
            # write day seperator if needed
            msg_date = datetime.utcfromtimestamp(
                round(float(msg["ts"]))).date()
            
            if msg_date != latest_date:
                document.ln()
                document.ln()
                document.set_font(
                    self._FONT_FAMILY_DEFAULT, 
                    size=self._FONT_SIZE_NORMAL, 
                    style="U")
                document.set_left_margin(self._MARGIN_LEFT)
                document.set_x(self._MARGIN_LEFT)
                document.write(
                    self._LINE_HEIGHT_DEFAULT, 
                    msg_date.strftime(self._FORMAT_DATETIME_SHORT))
                document.ln()
                latest_date = msg_date
            
            last_user_id = self._parse_message_and_write_pdf(
                document, 
                msg, 
                self._MARGIN_LEFT, 
                last_user_id
            )
            if "thread_ts" in msg and msg["thread_ts"] == msg["ts"]:
                thread_ts = msg["thread_ts"]
                
                if thread_ts in threads:
                    self._draw_line_for_threads(document)

                    for thread_msg in reversed(threads[thread_ts]):
                        last_user_id = self._parse_message_and_write_pdf(
                            document, 
                            thread_msg, 
                            self._MARGIN_LEFT + self._TAB_WIDTH, 
                            last_user_id
                        )
                    
                    self._draw_line_for_threads(document)
                
                last_user_id = None
    
        # store PDF
        filenamePdf = filename_base + ".pdf"
        print("Writing messages as PDF to file: " + filenamePdf)
        document.output(filenamePdf)
    