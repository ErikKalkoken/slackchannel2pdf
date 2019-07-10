import re
import html
import json
import os
import sys
from time import sleep
from datetime import datetime
import argparse
from time import sleep
import slack
import fpdf
from fpdf_ext import FPDF_ext


class MyFPDF(FPDF_ext):
    """Inheritance of FPDF class to add header and footers
    
    Public properties:
        page_title: text shown as title on every page
    """
    
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation=orientation, unit=unit, format=format)
        self._page_title = ""

    @property
    def page_title(self):
        return self._page_title
    
    @page_title.setter
    def page_title(self, text):
        """set text to appear as title on every page"""
        self._page_title = str(text)
    
    def header(self):
        """definition of custom header"""
        self.set_font(
            ChannelExporter._FONT_FAMILY_DEFAULT, 
            size=ChannelExporter._FONT_SIZE_NORMAL, 
            style="B"
            )
        self.cell(0, 0, self._page_title, 0, 1, "C")
        self.ln(ChannelExporter._LINE_HEIGHT_DEFAULT)
    
    def footer(self):
        """definition of custom footer"""
        self.set_y(-15)
        self.cell(0, 10, "Page " + str(self.page_no()) + " / {nb}", 0, 0, "C")

    def _write_info_table(self, table_def):        
        """write info table defined by dict"""
        cell_height = 10        
        for key, value in table_def.items():
            self.set_font(self.font_family, style="B")
            self.cell(50, cell_height, str(key), 1)
            self.set_font(self.font_family)
            self.cell(0, cell_height, str(value), 1)
            self.ln()


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

    Attachments and blocks (sections only for now) are supported.

    """    
    # general
    _VERSION = "0.1.0"
    
    # style and layout settings for PDF    
    _PAGE_ORIENTATION_DEFAULT = "portrait"
    _PAGE_FORMAT_DEFAULT = "a4"
    _PAGE_UNITS_DEFAULT = "mm"
    _FONT_FAMILY_DEFAULT = "Arial"
    _FONT_SIZE_NORMAL = 12
    _FONT_SIZE_LARGE = 14
    _FONT_SIZE_SMALL = 10
    _LINE_HEIGHT_DEFAULT = 6
    _LINE_HEIGHT_SMALL = 2
    _MARGIN_LEFT = 10
    _TAB_WIDTH = 4
    _FORMAT_DATE = '%Y-%b-%d'
    _FORMAT_DATETIME = '%Y-%b-%d %H:%M'
    _FORMAT_TIME = '%H:%M'

    # limits for fetching messages from Slack
    _MESSAGES_PER_PAGE = 200 # max message retrieved per request during paging
    _MAX_MESSAGES_PER_CHANNEL = 10000
    _MAX_MESSAGES_PER_THREAD = 500


    def __init__(self, slack_token, config=None):        
        """CONSTRUCTOR
        
        Args:
            slack_token: Ouath token to be used for all calls to the Slack API
                "TEST" can be provided to start test mode

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
            self._bot_names = dict()


    # *************************************************************************
    # Methods for fetching data from Slack API
    # *************************************************************************

    def _fetch_workspace_info(self):    
        """returns dict with info about current workspace"""
        
        # make sure slack client is set
        assert self._client is not None
        
        response = self._client.auth_test()
        assert response["ok"]
        return response
    

    def _fetch_user_names(self):    
        """returns dict of user names with user ID as key"""
        
        # make sure slack client is set
        assert self._client is not None

        response = self._client.users_list()
        assert response["ok"]    
        user_names = self._reduce_to_dict(
            response["members"], 
            "id", 
            "real_name", 
            "name"
            )        
        for user in user_names:
            user_names[user] = self._transform_encoding(user_names[user])
        
        return user_names


    def _fetch_channel_names(self):
        """returns dict of channel names with channel ID as key"""
        
        # make sure slack client is set
        assert self._client is not None
        
        response = self._client.conversations_list(
            types="public_channel,private_channel"
            )
        assert response["ok"]    
        channel_names = self._reduce_to_dict(
            response["channels"], 
            "id", 
            "name"
            )        
        for channel in channel_names:
            channel_names[channel] = self._transform_encoding(
                channel_names[channel]
                )
        
        return channel_names    


    def _fetch_messages_from_channel(self, channel_id, max_messages=None):
        """retrieve messages from a channel on Slack and return as list"""
        
        # make sure slack client is set
        assert self._client is not None
        
        if max_messages is None:
            max_messages = self._MAX_MESSAGES_PER_CHANNEL

        channel_name = self._channel_names[channel_id]
        messages_per_page = min(self._MESSAGES_PER_PAGE, max_messages)
        # get first page
        page = 1
        print("Fetching messages from channel - page {}".format(page))
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
            print("Fetching messages from channel - page {}".format(page))
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

        print("Fetched a total of {} messages from channel".format(
            len(messages_all)
            ))
        
        return messages_all


    def _read_array_from_json_file(self, filename):
        """reads a json file and returns its contents as array"""     
        filename += '.json'
        try:
            with open(filename, 'r') as f:
                arr = json.load(f)            
        except:
            print("ERROR: failed to read from {}".format(filename))
            arr = list()
                
        return arr


    def _write_array_to_json_file(self, arr, filename):
        """writes array to a json file"""     
        filename += '.json' 
        print("Writing file: name {}".format(filename))
        with open(filename , 'w', encoding='utf-8') as f:
            json.dump(
                arr, 
                f, 
                sort_keys=True, 
                indent=4, 
                ensure_ascii=False
                )        
    
    def _fetch_messages_from_thread(
        self, 
        channel_id, 
        thread_ts, 
        thread_num,
        max_messages=None):
        """retrieve messages from a Slack thread and return as list"""
        
        # make sure slack client is set
        assert self._client is not None

        if max_messages is None:
            max_messages = self._MAX_MESSAGES_PER_THREAD
        
        messages_per_page = min(self._MESSAGES_PER_PAGE, max_messages)
        # get first page
        page = 1        
        print("Fetching messages from thread {} - page {}".format(
            thread_num,
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
            print("Fetching messages from thread {} - page {}".format(
                thread_num,
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
        thread_num = 0
        thread_messages_total = 0
        for msg in messages:
            if "thread_ts" in msg and msg["thread_ts"] == msg["ts"]:
                thread_ts = msg["thread_ts"]
                thread_num += 1
                thread_messages = self._fetch_messages_from_thread(                    
                    channel_id, 
                    thread_ts,
                    thread_num,
                    max_messages
                )            
                threads[thread_ts] = thread_messages
                thread_messages_total += len(thread_messages)
        
        print("Fetched a total of {} messages from {} threads".format(
            thread_messages_total,                
            thread_num
            ))
        
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


    def _fetch_bot_names_for_messages(self, messages, threads):
        """Fetches bot names from API for provided messages 
        
        Will only fetch names for bots that never appeared with a username
        in any message (lazy approach since calls to bots_info are very slow)
        """        
        
        # make sure slack client is set
        assert self._client is not None
        
        # collect bot_ids without user name from messages
        bot_ids = list()
        bot_names = dict()
        for msg in messages:
            if "bot_id" in msg: 
                bot_id = msg["bot_id"]
                if "username" in msg:
                    bot_names[bot_id] = self._transform_encoding(msg["username"])
                else:
                    bot_ids.append(bot_id)

        # collect bot_ids without user name from thread messages
        for thread_messages in threads:
            for msg in thread_messages:
                if "bot_id" in msg: 
                    bot_id = msg["bot_id"]
                    if "username" in msg:
                        bot_names[bot_id] = self._transform_encoding(msg["username"])
                    else:
                        bot_ids.append(bot_id)

        # Find bot IDs that are not in bot_names
        bot_ids = set(bot_ids).difference(bot_names.keys())
        
        # collect bot names from API if needed        
        if len(bot_ids) > 0:
            print("Fetching names for {} bots".format(len(bot_ids)))
            for bot_id in bot_ids:
                response = self._client.bots_info(bot=bot_id)
                if response["ok"]:
                    bot_names[bot_id] = self._transform_encoding(response["bot"]["name"])
                    sleep(1)   # need to wait 1 sec before next call due to rate limits
        
        return bot_names
                        


    # *************************************************************************
    # Methods for parsing and transforming Slack messages
    # *************************************************************************

    def _transform_encoding(self, text):
        """adjust encoding to latin-1 and transform HTML entities"""        
        text2 = html.unescape(text)
        text2 = text2.encode('latin-1', 'replace').decode('latin-1')
        return text2
    
    def _transform_text(self, text, use_mrkdwn=False):    
        """transforms mrkdwn text into HTML text for PDF output
        
        Main method to resolve all mrkdwn, e.g. <C12345678>, <!here>, *bold*
        Will resolve channel and user IDs to their names if possible
        Returns string with rudimentary HTML for formatting and links

        Attr:
            text: text string to be transformed
            use_mrkdwn: will transform mrkdwn if set to true

        Returns:
            transformed text string with HTML formatting
        """
        
        def replace_mrkdwn_in_text(matchObj):
            """inline function returns replacement string for re.sub            
            
            This function does the actual resolving of IDs and mrkdwn key words
            """             
            match = matchObj.group(1)

            id_chars = match[0:2]
            id_raw = match[1:len(match)]
            parts = id_raw.split("|", 1)
            id = parts[0]

            make_bold = True
            if id_chars == "@U" or id_chars == "@W":
                # match is a user ID
                if id in self._user_names:
                    replacement = "@" + self._user_names[id]
                else:
                    replacement = "@unknown_{}".format(id)
            
            elif id_chars == "#C":
                # match is a channel ID
                if id in self._channel_names:
                    replacement = "#" + self._channel_names[id]
                else:
                    replacement = "#unknown_{}".format(id)
            
            elif match[0:9] == "!subteam":
                # match is a user group ID
                replacement = "@usergroup_dummy"
            
            elif match[0:1] == "!":
                # match is a special mention
                if id == "here":
                    replacement = "@here"
                
                elif id == "channel":
                    replacement = "@channel"
                
                elif id == "everyone":
                    replacement = "@everyone"                    
            
                elif match[0:5] == "!date":
                    make_bold = False
                    date_parts = match.split("^")                    
                    if len(date_parts) > 1:
                        replacement = self._get_datetime_formatted_str(
                            date_parts[1]
                            )
                    else:
                        replacement = "(failed to parse date)"

                else:
                    replacement = "unknown_{}". format(id)
            
            else:
                # match is an URL
                link_parts = match.split("|")
                if len(link_parts) == 2:
                    url = link_parts[0]
                    text = link_parts[1] 
                else:
                    url = match
                    text = match  

                make_bold = False
                replacement = ('<a href="' 
                        + url 
                        + '">' 
                        + text
                        + '</a>')

            if make_bold:
                replacement =  '<b>' + replacement + '</b>'

            return replacement


        # pass 1 - adjust encoding to latin-1 and transform HTML entities        
        s2 = self._transform_encoding(text)
        
        # if requested try to transform mrkdwn in text
        if use_mrkdwn:

            # pass 2 - transform mrkdwns with brackets
            s2 = re.sub(
                r'<(.*?)>',
                replace_mrkdwn_in_text,
                s2
                )

            # pass 3 - transform formatting mrkdwns

            # bold
            s2 = re.sub(
                r'\*(.+)\*',
                r'<b>\1</b>',
                s2
                )

            s2 = re.sub(
                r'\b_(.+)_\b',
                r'<i>\1</i>',
                s2
                )

            # code
            s2 = re.sub(
                r'`(.*)`',
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
            round(float(ts))).strftime(self._FORMAT_TIME)


    def _parse_message_and_write_to_pdf(
            self, 
            document, 
            msg, 
            margin_left, 
            last_user_id):
        """parse a message and write it to the PDF"""
        
        if "user" in msg:
            user_id = msg["user"]
            is_bot = False
            if user_id in self._user_names:
                user_name = self._user_names[user_id]
            else:
                user_name = "unknown_user_{}".format(user_id)
        
        elif "bot_id" in msg:
            user_id = msg["bot_id"]
            is_bot = True
            if "username" in msg:
                user_name = self._transform_encoding(msg["username"])
            elif user_id in self._bot_names:
                user_name = self._bot_names[user_id]
            else:
                user_name = "unknown_bot_{}".format(user_id)
        else:
            user_name = None
            
        if user_name is not None: 
            # start again on the left border        
            document.set_left_margin(margin_left)
            document.set_x(margin_left)
            
            if last_user_id != user_id:
                # write user name and date only when user switches
                document.ln(self._LINE_HEIGHT_SMALL)
                document.set_font(
                    self._FONT_FAMILY_DEFAULT, 
                    size=self._FONT_SIZE_NORMAL, 
                    style="B")
                document.write(self._LINE_HEIGHT_DEFAULT, user_name + " ")                
                document.set_font(
                    self._FONT_FAMILY_DEFAULT, 
                    size=self._FONT_SIZE_SMALL)
                if is_bot:                    
                    document.set_text_color(100, 100, 100)
                    document.write(self._LINE_HEIGHT_DEFAULT, "App ")
                    document.set_text_color(0)
                datetime_str = self._get_datetime_formatted_str(msg["ts"])
                document.write(self._LINE_HEIGHT_DEFAULT, datetime_str)
                document.ln()            
            
            if "text" in msg and len(msg["text"]) > 0:
                document.set_font(
                    self._FONT_FAMILY_DEFAULT, 
                    size=self._FONT_SIZE_NORMAL)                            
                document.write_html(
                    self._LINE_HEIGHT_DEFAULT, 
                    self._transform_text(
                        msg["text"], 
                        msg["mrkdwn"] if "mrkdwn" in msg else True
                    ))
                document.ln()

            if "reactions" in msg:
                 # draw reactions                
                for reaction in msg["reactions"]:        
                    document.set_left_margin(margin_left + self._TAB_WIDTH)
                    document.set_x(margin_left + self._TAB_WIDTH)
                    document.set_font(
                        self._FONT_FAMILY_DEFAULT, 
                        size=self._FONT_SIZE_NORMAL)                           
                    document.write_html(
                        self._LINE_HEIGHT_DEFAULT, 
                        ("[" 
                            + reaction["name"]
                            + "] ("
                            + str(reaction["count"])
                            + "):"))
                    document.ln()
                    
                    # convert user IDs to names
                    users_with_names = list()
                    for user in reaction["users"]:
                        if user in self._user_names:
                            user_name = self._user_names[user]
                        else:
                            user_name = "unknown_user_" + user

                        users_with_names.append('<b>' + user_name + '</b>')

                    document.set_left_margin(margin_left + self._TAB_WIDTH + self._TAB_WIDTH)
                    document.set_x(margin_left + self._TAB_WIDTH + self._TAB_WIDTH)                    
                    document.write_html(
                        self._LINE_HEIGHT_DEFAULT, 
                        ", ".join(users_with_names)
                    )
                    document.ln()
                
                document.ln(self._LINE_HEIGHT_SMALL)

            if "files" in msg:
                # draw files
                document.set_left_margin(margin_left + self._TAB_WIDTH)
                document.set_x(margin_left + self._TAB_WIDTH)

                for file in msg["files"]:
                    text = ('[' 
                        + file["pretty_type"]
                        + ' file: <b>'
                        + file["name"] 
                        + '</b>'
                        + ']')
                    document.set_font(
                        self._FONT_FAMILY_DEFAULT, 
                        size=self._FONT_SIZE_NORMAL)
                    document.write_html(self._LINE_HEIGHT_DEFAULT, text)
                    document.ln()

            if "attachments" in msg:
                # draw attachments                                
                document.set_left_margin(margin_left + self._TAB_WIDTH)
                document.set_x(margin_left + self._TAB_WIDTH)
                
                # draw normal text attachments
                for attach in msg["attachments"]:            
                        
                    if "mrkdwn_in" in attach:
                        mrkdwn_in = attach["mrkdwn_in"]
                    else:
                        mrkdwn_in = []
                    
                    if "pretext" in attach:
                        document.set_left_margin(margin_left)
                        document.set_x(margin_left)
                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, 
                            size=self._FONT_SIZE_NORMAL)
                        document.write_html(
                            self._LINE_HEIGHT_DEFAULT, 
                            self._transform_text(
                                attach["pretext"], 
                                "pretext" in mrkdwn_in
                            ))
                        document.set_left_margin(
                            margin_left + self._TAB_WIDTH)
                        document.set_x(margin_left + self._TAB_WIDTH)
                        document.ln()

                    document.ln(self._LINE_HEIGHT_SMALL)

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
                        title_text = self._transform_text(
                            attach["title"], 
                            "title" in mrkdwn_in
                            )

                        # add link to title if defined
                        if "title_link" in attach:
                            title_text = ('<a href="' + attach["title_link"] 
                                + '">' + title_text 
                                + '</a>')
                        
                        # add bold formatting to title
                        title_text = '<b>' + title_text + '</b>'

                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, 
                            size=self._FONT_SIZE_NORMAL)
                        document.write_html(
                            self._LINE_HEIGHT_DEFAULT, 
                            title_text)
                        document.ln()
                    
                    if "text" in attach:
                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, 
                            size=self._FONT_SIZE_NORMAL)
                        document.write_html(
                            self._LINE_HEIGHT_DEFAULT, 
                            self._transform_text(
                                attach["text"],
                                "text" in mrkdwn_in
                            ))
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
                            document.write_html(
                                self._LINE_HEIGHT_DEFAULT, 
                                self._transform_text(
                                    field["value"], 
                                    "fields" in mrkdwn_in
                                ))
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
                        image_url_html = ('<a href="' 
                            + attach["image_url"] 
                            + '">[Image]</a>')
                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, 
                            size=self._FONT_SIZE_NORMAL)
                        document.write_html(
                            self._LINE_HEIGHT_DEFAULT, 
                            image_url_html)
                        document.ln()

                    # action attachments
                    if "actions" in attach:
                        for action in attach["actions"]:                            
                            document.set_font(
                                self._FONT_FAMILY_DEFAULT, 
                                size=self._FONT_SIZE_SMALL)                            
                            document.write_html(
                                self._LINE_HEIGHT_DEFAULT, 
                                ("[" 
                                    + self._transform_text(action["text"]) 
                                    + "] "))
                        
                        document.ln()
                
                document.ln(self._LINE_HEIGHT_SMALL)

            if "blocks" in msg:                                
                document.set_left_margin(margin_left + self._TAB_WIDTH)
                document.set_x(margin_left + self._TAB_WIDTH)
                
                for layout_block in msg["blocks"]:
                    type = layout_block["type"]
                    document.ln(self._LINE_HEIGHT_SMALL)

                    # section layout blocks
                    if type == "section":                        
                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, 
                            size=self._FONT_SIZE_NORMAL)
                        document.write_html(
                            self._LINE_HEIGHT_DEFAULT, 
                            self._transform_text(
                                layout_block["text"]["text"],
                                layout_block["text"]["type"] == "mrkdwn"
                            ))
                        document.ln()

                        if "fields" in layout_block:
                            for field in layout_block["fields"]:
                                document.set_font(
                                    self._FONT_FAMILY_DEFAULT, 
                                    size=self._FONT_SIZE_NORMAL)
                                document.write_html(
                                    self._LINE_HEIGHT_DEFAULT, 
                                    self._transform_text(
                                        field["text"], 
                                        field["type"] == "mrkdwn" 
                                    ))
                                document.ln()
                    
                document.ln(self._LINE_HEIGHT_SMALL)
                
        else:
            user_id = None
            print("WARN: Can not process message with ts {}".format(msg["ts"]))

        return user_id   


    def _write_messages_to_pdf(self, document, messages, threads):
        """writes messages with their threads to the PDF document"""
        last_user_id = None
        last_date = None
        last_page = None
        
        if len(messages) > 0:
            messages = sorted(messages, key=lambda k: k['ts'])
            for msg in messages:
                
                # write day seperator if needed
                msg_date = datetime.utcfromtimestamp(
                    round(float(msg["ts"]))).date()
                
                if msg_date != last_date:
                    document.ln(self._LINE_HEIGHT_SMALL)
                    document.ln(self._LINE_HEIGHT_SMALL)
                    document.set_font(
                        self._FONT_FAMILY_DEFAULT, 
                        size=self._FONT_SIZE_NORMAL
                        )
                    
                    # draw divider line for next day
                    width = document.fw - 2 * self._MARGIN_LEFT
                    x1 = self._MARGIN_LEFT
                    x2 = x1 + width
                    y1 = document.get_y() + 3                
                    document.line(x1, y1, x2, y1)
                    
                    # stamp date on divider
                    date_text = msg_date.strftime(self._FORMAT_DATE)
                    width = document.get_string_width(date_text)
                    cell_x = (x2 - x1 - width) / 2
                    cell_y = y1                
                    document.cell(cell_x)
                    document.set_fill_color(255, 255, 255)
                    document.cell(
                        30,
                        self._LINE_HEIGHT_DEFAULT,
                        date_text, 
                        0,
                        0,
                        "C",
                        True
                    )
                    
                    document.ln()
                    last_date = msg_date
                    last_user_id = None     # repeat user name for new day
                
                # repeat user name for new page
                if last_page != document.page_no():
                    last_user_id = None
                    last_page = document.page_no()

                last_user_id = self._parse_message_and_write_to_pdf(
                    document, 
                    msg, 
                    self._MARGIN_LEFT, 
                    last_user_id
                )
                if "thread_ts" in msg and msg["thread_ts"] == msg["ts"]:
                    thread_ts = msg["thread_ts"]
                    
                    if thread_ts in threads:
                        thread_messages = threads[thread_ts]                       
                        last_user_id = None                                                
                        thread_messages = sorted(
                            thread_messages, 
                            key=lambda k: k['ts']
                            )
                        for thread_msg in thread_messages:                            
                            if thread_msg['ts'] != thread_msg['thread_ts']:
                                last_user_id = self._parse_message_and_write_to_pdf(
                                    document, 
                                    thread_msg, 
                                    self._MARGIN_LEFT + self._TAB_WIDTH, 
                                    last_user_id
                                )
                        
                    last_user_id = None
        else:
            document.set_font(
                self._FONT_FAMILY_DEFAULT, 
                size=self._FONT_SIZE_NORMAL
                )
            document.write(
                self._LINE_HEIGHT_DEFAULT, 
                "This channel is empty", 
                "I"
            )


    def run(
        self, 
        channel_input, 
        max_messages=None, 
        write_raw_data=False,
        page_orientation="portrait",
        page_format="a4"
        ):
        """export all message from a channel and store them in a PDF
        
        Args:
            channel_input: Name or ID of channel to retrieve messages from
            max_messages: maximum number of messages to retrieve
            write_raw_data: will safe data recveived from API to files if true
            page_orientation: orientation of pages  as defined in FPDF class,
            page_format: format of pages, see as defined in FPDF class
        """
                
        # fetch messages
        team_name = self._workspace_info["team"]
        if self._client is not None:            
            # if we have a client fetch data from Slack            
            if channel_input.upper() in self._channel_names:
                channel_id = channel_input.upper()
            else:
                # flip channel_names since channel names are unique
                channel_names_ids = {v:k for k,v in self._channel_names.items()}
                if channel_input.lower() not in channel_names_ids:
                    raise RuntimeError("Unknown channel '" 
                        + channel_input 
                        + "' on " 
                        + team_name)                    
                else:
                    channel_id = channel_names_ids[channel_input.lower()]
            
            channel_name = self._channel_names[channel_id]

            print("Retrieving messages from " 
                + team_name 
                + " / " 
                + channel_name 
                + " ...")
            
            messages = self._fetch_messages_from_channel(
                channel_id, 
                max_messages
                )
            threads = self._fetch_threads_from_messages(
                channel_id, 
                messages
                )
            self._bot_names = self._fetch_bot_names_for_messages(
                messages, 
                threads
                )
            
            filename_base = team_name + "_" + channel_name
            if write_raw_data:
                # write raw data received from Slack API to file                
                self._write_array_to_json_file(
                    self._user_names, 
                    filename_base + "_users"
                    )
                self._write_array_to_json_file(
                    self._bot_names, 
                    filename_base + "_bots"
                    )
                self._write_array_to_json_file(
                    self._channel_names, 
                    filename_base + "_channels"
                    )
                self._write_array_to_json_file(
                    messages, 
                    filename_base + "_messages"
                    )
                if len(threads) > 0:
                    self._write_array_to_json_file(
                        threads, filename_base + "_threads"
                        )
        else:
            # if we don't have a client we will try to fetch from a file
            # this is used for testing
            filename_base = "test/" + str(channel_input)
            messages = self._read_array_from_json_file(filename_base 
                + "_messages")
            threads = self._read_array_from_json_file(filename_base 
                + "_threads")
        
        # create PDF
        document = MyFPDF(
            page_orientation, 
            self._PAGE_UNITS_DEFAULT, 
            page_format
        )
        document.alias_nb_pages()
        document.add_page()

        # compile all values
        workspace_name = self._workspace_info["team"]
        channel_name = self._channel_names[channel_id]
        creation_date = datetime.utcnow()
        creation_datetime_str = creation_date.strftime(self._FORMAT_DATETIME)        
        if self._workspace_info["user_id"] in self._user_names:
            author = self._user_names[self._workspace_info["user_id"]]
        else:
            author = "unknown_user_" + self._workspace_info["user_id"]
        
        # count all messages including threads
        message_count = len(messages)
        if len(threads) > 0:
            for thread_ts, thread_messages in threads.items():
                message_count += len(thread_messages) -1

        # find start and end date based on messages
        ts_extract = [d['ts'] for d in messages]
        ts_min = min(float(s) for s in ts_extract)
        ts_max = max(float(s) for s in ts_extract)
        start_date = datetime.utcfromtimestamp(float(ts_min))
        end_date = datetime.utcfromtimestamp(float(ts_max))

        # set variables for title, header, footer
        title = "Slack channel PDF export" 
        sub_title = workspace_name + " / " + channel_name
        page_title = title + "from " + sub_title
                
        # set general properties in document        
        document.set_author(author)
        document.set_creator("Channel Export")
        document.set_title(title)
        document.set_creation_date(creation_date)
        document.set_subject(sub_title)                        
        document.page_title = page_title
        
        # write title on first page        
        document.set_font(
            self._FONT_FAMILY_DEFAULT, 
            size=self._FONT_SIZE_LARGE, 
            style="B"
            )
        document.cell(0, 0, title, 0, 1, "C")
        document.ln(self._LINE_HEIGHT_DEFAULT)
        
        document.set_font(
            self._FONT_FAMILY_DEFAULT, 
            size=self._FONT_SIZE_NORMAL, 
            style="B"
            )
        document.cell(0, 0, sub_title, 0, 1, "C")
        document.ln(self._LINE_HEIGHT_DEFAULT)

        # write info block after title
        table_def = {
            "Slack workspace": workspace_name,
            "Channel": channel_name,            
            "Exported at": creation_datetime_str,
            "Exported by": author,
            "Start date": start_date.strftime(self._FORMAT_DATETIME),
            "End date": end_date.strftime(self._FORMAT_DATETIME),
            "Messages": message_count,
            "Threads": len(threads.keys()) if len(threads) > 0 else 0
        }
        document._write_info_table(table_def)
        
        # write messages to PDF
        self._write_messages_to_pdf(document, messages, threads)
        
        # store PDF
        filenamePdf = filename_base + ".pdf"
        print("Writing PDF file: " + filenamePdf)
        document.output(filenamePdf)
    
        
    
def main():
    """Implements the arg parser and starts the channelexporter with its input"""

    # main arguments
    parser = argparse.ArgumentParser(
        description = "This program exports the text of a Slack channel to a PDF file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument(
        "token",         
        help = "Slack Oauth token"
        )
    parser.add_argument(        
        "channel", 
        help = "Name or ID of channel to export"
        )
    
    # PDF file
    parser.add_argument(        
        "-d",
        "--destination",         
        help = "Specify a destination path to store the PDF file. (TBD)",
        default = "."
        )
    
    # formatting
    parser.add_argument(        
        "--page-orientation",         
        help = "Orientation of PDF pages",
        choices = ["portrait", "landscape"],
        default = ChannelExporter._PAGE_ORIENTATION_DEFAULT
        )
    parser.add_argument(        
        "--page-format",         
        help = "Format of PDF pages",
        choices = ["a3", "a4", "a5", "letter", "legal"],
        default = ChannelExporter._PAGE_FORMAT_DEFAULT
        )
    parser.add_argument(
        "--timezone",         
        help = "timezone for rending all dates (TBD)",
        default = "portrait"
        )
    parser.add_argument(
        "--tz-offset",         
        help = "timezone offset (TBD)",
        default = "portrait"
        )    

    # standards
    parser.add_argument(        
        "--version",         
        help="show the program version and exit", 
        action="version", 
        version=ChannelExporter._VERSION
        )    

    # exporter config
    parser.add_argument(        
        "--max-messages",         
        help = "max number of messages to export",
        type = int
        )

    # Developer needs
    parser.add_argument(        
        "--write-raw-data",
        help = "will also write all raw data returned from the API to files,"\
            + " e.g. messages.json with all messages",                
        action = "store_const",
        const = True
        )    

    args = parser.parse_args()

    if "version" in args:
        print(ChannelExporter._VERSION)            
    else:        
        exporter = ChannelExporter(args.token)
        exporter.run(
            args.channel, 
            args.max_messages, 
            args.write_raw_data == True
        )
    

if __name__ == '__main__':
    main()