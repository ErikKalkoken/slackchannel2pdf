# Copyright 2019 Erik Kalkoken
#
# Licensed under MIT license. See attached file for details
#
# This package contains the main functionality of slackchannel2pdf
# User interfaces to this tool (e.g. commnad line) are in a separate package
#

import html
import inspect
import json
import os
import re
from time import sleep

from babel import Locale, UnknownLocaleError
from babel.dates import format_date, format_datetime, format_time
from babel.numbers import format_number
from datetime import datetime, timedelta
import pytz
import slack
from tzlocal import get_localzone

from . import __version__
from .fpdf_ext import FPDF_ext


def reduce_to_dict(arr, key_name, col_name_primary, col_name_secondary=None):
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
            elif col_name_secondary is not None and col_name_secondary in item:
                arr2[key] = item[col_name_secondary]
    return arr2


class MyFPDF(FPDF_ext):
    """Inheritance of FPDF class to add header and footers

    Public properties:
        page_title: text shown as title on every page
    """

    def __init__(self, orientation="P", unit="mm", format="A4"):
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
            SlackChannelExporter._FONT_FAMILY_DEFAULT,
            size=SlackChannelExporter._FONT_SIZE_NORMAL,
            style="B",
        )
        self.cell(0, 0, self._page_title, 0, 1, "C")
        self.ln(SlackChannelExporter._LINE_HEIGHT_DEFAULT)

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


class SlackChannelExporter:
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

    # style and layout settings for PDF
    _PAGE_ORIENTATION_DEFAULT = "portrait"
    _PAGE_FORMAT_DEFAULT = "a4"
    _PAGE_UNITS_DEFAULT = "mm"
    _FONT_FAMILY_DEFAULT = "NotoSans"
    _FONT_FAMILY_MONO_DEFAULT = "NotoSansMono"
    _FONT_SIZE_NORMAL = 12
    _FONT_SIZE_LARGE = 14
    _FONT_SIZE_SMALL = 10
    _LINE_HEIGHT_DEFAULT = 6
    _LINE_HEIGHT_SMALL = 2
    _MARGIN_LEFT = 10
    _TAB_WIDTH = 4

    # limits for fetching messages from Slack
    _MESSAGES_PER_PAGE = 200  # max message retrieved per request during paging
    _MAX_MESSAGES_PER_CHANNEL = 10000

    FALLBACK_LOCALE = "en"

    def __init__(self, slack_token, my_tz=None, my_locale=None, add_debug_info=False):
        """CONSTRUCTOR

        Args:
            slack_token: OAuth token to be used for all calls to the Slack API
                "TEST" can be provided to start test mode
            my_tz: override system's timezone (pytz.BaseTzInfo object)
            my_locale: override system's locale (locale string, e.g. 'de_DE')
            add_debug_info: wether to add debug info to message output

        """
        if slack_token is None:
            raise ValueError("slack_token can not be null")

        # output welcome message
        print(f"slackchannel2pdf v{__version__} by Erik Kalkoken")
        print("")

        # load information for current Slack workspace
        if slack_token != "TEST":
            self._client = slack.WebClient(token=slack_token)
            self._workspace_info = self._fetch_workspace_info()
            self._user_names = self._fetch_user_names()
            self._channel_names = self._fetch_channel_names()
            self._usergroup_names = self._fetch_usergroup_names()

            # set author
            if "user_id" in self._workspace_info:
                author_id = self._workspace_info["user_id"]
                if self._workspace_info["user_id"] in self._user_names:
                    author = self._user_names[author_id]
                else:
                    author = "unknown_user_" + self._workspace_info["user_id"]
            else:
                author_id = None
                author = "unknown user"

        else:
            # if started with TEST parameter class properties will be
            # initialized empty and need to be set manually in test setup
            self._client = None
            self._workspace_info = dict()
            self._user_names = dict()
            self._channel_names = dict()
            self._usergroup_names = dict()
            self._bot_names = dict()
            author_id = None
            author = "test user"

        self._author = author

        # output welcome message and inform about current parameters
        print()
        print("Welcome " + self._author)

        # get timezone and local for author from Slack
        if author_id is not None:
            author_info = self._fetch_user_info(author_id)
        else:
            author_info = None

        # set timezone
        # check if overridden timezone is valid
        if my_tz is not None:
            if not isinstance(my_tz, pytz.BaseTzInfo):
                raise TypeError("my_tz must be of type pytz")
        # if not overridden use timezone info from author on Slack if available
        # else use local time of this system
        else:
            if author_info is not None:
                try:
                    my_tz = pytz.timezone(author_info["tz"])
                except pytz.exceptions.UnknownTimeZoneError:
                    print("WARN: Could not use timezone info from Slack")
                    my_tz = get_localzone()
            else:
                my_tz = get_localzone()

        self._my_tz = my_tz
        print(f"Timezone is: {str(my_tz)}")

        # set locale
        # check if overridden locale is valid
        if my_locale is not None:
            if not isinstance(my_locale, Locale):
                raise TypeError("my_locale must be a babel Locale object")
        # if not overridden use timezone info from author on Slack if available
        # else use local time of this system
        else:
            if author_info is not None:
                try:
                    my_locale = Locale.parse(author_info["locale"], sep="-")
                except UnknownLocaleError:
                    print("WARN: Could not use locale info from Slack")
                    my_locale = Locale.default()

            else:
                my_locale = Locale.default()

        self._my_locale = my_locale
        print(f"Locale is: {my_locale.get_display_name()} [{self._my_locale}]")

        # validate add_debug_info
        if type(add_debug_info) != bool:
            raise ValueError("add_debug_info must be bool")
        self._add_debug_info = add_debug_info

        if add_debug_info:
            print("Adding DEBUG info to PDF")

    # *************************************************************************
    # Methods for fetching data from Slack API
    # *************************************************************************

    def _fetch_workspace_info(self):
        """returns dict with info about current workspace"""

        # make sure slack client is set
        assert self._client is not None

        print("Fetching workspace info from Slack...")
        res = self._client.auth_test()
        response = res.data
        assert response["ok"]
        return response

    def _fetch_user_names(self):
        """returns dict of user names with user ID as key"""

        # make sure slack client is set
        assert self._client is not None

        print("Fetching users for workspace...")
        response = self._client.users_list()
        assert response["ok"]
        user_names = reduce_to_dict(response["members"], "id", "real_name", "name")
        for user in user_names:
            user_names[user] = self._transform_encoding(user_names[user])

        return user_names

    def _fetch_user_info(self, user_id):
        """returns dict of user info for user ID incl. locale"""

        # make sure slack client is set
        assert self._client is not None

        print("Fetching user info for author...")
        response = self._client.users_info(user=user_id, include_locale=1)
        assert response["ok"]
        return response["user"]

    def _fetch_channel_names(self):
        """returns dict of channel names with channel ID as key"""

        # make sure slack client is set
        assert self._client is not None

        print("Fetching channels for workspace...")
        response = self._client.conversations_list(
            types="public_channel,private_channel"
        )
        assert response["ok"]
        channel_names = reduce_to_dict(response["channels"], "id", "name")
        for channel in channel_names:
            channel_names[channel] = self._transform_encoding(channel_names[channel])

        return channel_names

    def _fetch_usergroup_names(self):
        """returns dict of usergroup names with usergroup ID as key"""

        # make sure slack client is set
        assert self._client is not None

        print("Fetching usergroups for workspace...")
        response = self._client.usergroups_list()
        assert response["ok"]
        usergroup_names = reduce_to_dict(response["usergroups"], "id", "handle")
        for usergroup in usergroup_names:
            usergroup_names[usergroup] = self._transform_encoding(
                usergroup_names[usergroup]
            )

        return usergroup_names

    def _fetch_messages_from_channel(
        self, channel_id, max_messages, oldest=None, latest=None
    ):
        """retrieve messages from a channel on Slack and return as list"""

        # make sure slack client is set
        assert self._client is not None

        messages_per_page = min(self._MESSAGES_PER_PAGE, max_messages)
        # get first page
        page = 1
        print(f"Fetching messages from channel - page {page}")
        oldest_ts = str(oldest.timestamp()) if oldest is not None else 0
        latest_ts = str(latest.timestamp()) if latest is not None else 0
        response = self._client.conversations_history(
            channel=channel_id,
            limit=messages_per_page,
            oldest=oldest_ts,
            latest=latest_ts,
        )
        assert response["ok"]
        messages_all = response["messages"]

        # get additional pages if below max message and if they are any
        while len(messages_all) < max_messages and response["has_more"]:
            page += 1
            print(f"Fetching messages from channel - page {page}")
            sleep(1)  # need to wait 1 sec before next call due to rate limits
            # allow smaller page sized to fetch final page
            page_limit = min(messages_per_page, max_messages - len(messages_all))
            response = self._client.conversations_history(
                channel=channel_id,
                limit=page_limit,
                oldest=oldest_ts,
                latest=latest_ts,
                cursor=response["response_metadata"]["next_cursor"],
            )
            assert response["ok"]
            messages = response["messages"]
            messages_all = messages_all + messages

        print(
            f"Fetched a total of "
            f"{format_number(len(messages_all), locale=self._my_locale)}"
            f" messages from channel {self._channel_names[channel_id]}"
        )
        return messages_all

    def _read_array_from_json_file(self, filename, quiet=False):
        """reads a json file and returns its contents as array"""
        filename += ".json"
        if not os.path.isfile(filename):
            if quiet is False:
                print(f"WARN: file does not exist: {filename}")
            arr = list()
        else:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    arr = json.load(f)
            except Exception as e:
                if quiet is False:
                    print(f"WARN: failed to read from {filename}: ", e)
                arr = list()

        return arr

    def _write_array_to_json_file(self, arr, filename):
        """writes array to a json file"""
        filename += ".json"
        print(f"Writing file: name {filename}")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(arr, f, sort_keys=True, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"ERROR: failed to write to {filename}: ", e)

    def _fetch_messages_from_thread(
        self, channel_id, thread_ts, thread_num, max_messages, oldest=None, latest=None
    ):
        """retrieve messages from a Slack thread and return as list"""

        # make sure slack client is set
        assert self._client is not None

        messages_per_page = min(self._MESSAGES_PER_PAGE, max_messages)
        # get first page
        page = 1
        print(f"Fetching messages from thread {thread_num} - page {page}")
        oldest_ts = str(oldest.timestamp()) if oldest is not None else 0
        latest_ts = str(latest.timestamp()) if latest is not None else 0
        response = self._client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            limit=messages_per_page,
            oldest=oldest_ts,
            latest=latest_ts,
        )
        assert response["ok"]
        messages_all = response["messages"]

        # get additional pages if below max message and if they are any
        while (
            len(messages_all) + messages_per_page <= max_messages
            and response["has_more"]
        ):
            page += 1
            print(f"Fetching messages from thread {thread_num} - page {page}")
            sleep(1)  # need to wait 1 sec before next call due to rate limits
            response = self._client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                limit=messages_per_page,
                oldest=oldest_ts,
                latest=latest_ts,
                cursor=response["response_metadata"]["next_cursor"],
            )
            assert response["ok"]
            messages = response["messages"]
            messages_all = messages_all + messages

        return messages_all

    def _fetch_threads_from_messages(
        self, channel_id, messages, max_messages, oldest=None, latest=None
    ):
        """returns threads for all message from for a channel as dict"""

        threads = dict()
        thread_num = 0
        thread_messages_total = 0
        for msg in messages:
            if "thread_ts" in msg and msg["thread_ts"] == msg["ts"]:
                thread_ts = msg["thread_ts"]
                thread_num += 1
                thread_messages = self._fetch_messages_from_thread(
                    channel_id, thread_ts, thread_num, max_messages, oldest, latest
                )
                threads[thread_ts] = thread_messages
                thread_messages_total += len(thread_messages)

        if thread_messages_total > 0:
            print(
                f"Fetched a total of "
                f"{format_number(thread_messages_total, locale=self._my_locale)}"
                f" messages from {thread_num} threads"
            )
        else:
            print("This channel has no threads")

        return threads

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
            print(f"Fetching names for {len(bot_ids)} bots")
            for bot_id in bot_ids:
                response = self._client.bots_info(bot=bot_id)
                if response["ok"]:
                    bot_names[bot_id] = self._transform_encoding(
                        response["bot"]["name"]
                    )
                    sleep(1)  # need to wait 1 sec before next call due to rate limits

        return bot_names

    # *************************************************************************
    # Methods for parsing and transforming Slack messages
    # *************************************************************************

    def _transform_encoding(self, text):
        """adjust encoding to latin-1 and transform HTML entities"""
        text2 = html.unescape(text)
        text2 = text2.encode("utf-8", "replace").decode("utf-8")
        text2 = text2.replace("\t", "    ")
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
            id_raw = match[1 : len(match)]
            parts = id_raw.split("|", 1)
            id = parts[0]

            make_bold = True
            if id_chars == "@U" or id_chars == "@W":
                # match is a user ID
                if id in self._user_names:
                    replacement = "@" + self._user_names[id]
                else:
                    replacement = f"@user_{id}"

            elif id_chars == "#C":
                # match is a channel ID
                if id in self._channel_names:
                    replacement = "#" + self._channel_names[id]
                else:
                    replacement = f"#channel_{id}"

            elif match[0:9] == "!subteam^":
                # match is a user group ID
                match2 = re.match(r"!subteam\^(S[A-Z0-9]+)", match)
                if match2 is not None and len(match2.groups()) == 1:
                    id = match2.group(1)
                    if id in self._usergroup_names:
                        usergroup_name = self._usergroup_names[id]
                    else:
                        usergroup_name = f"usergroup_{id}"
                else:
                    usergroup_name = "usergroup_unknown"
                replacement = "@" + usergroup_name

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
                        replacement = self._get_datetime_formatted_str(date_parts[1])
                    else:
                        replacement = "(failed to parse date)"

                else:
                    replacement = f"@special_{id}"

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
                replacement = f'<a href="{url}">{text}</a>'

            if make_bold:
                replacement = f"<b>{replacement}</b>"

            return replacement

        # pass 1 - adjust encoding to latin-1 and transform HTML entities
        s2 = self._transform_encoding(text)

        # if requested try to transform mrkdwn in text
        if use_mrkdwn:

            # pass 2 - transform mrkdwns with brackets
            s2 = re.sub(r"<(.*?)>", replace_mrkdwn_in_text, s2)

            # pass 3 - transform formatting mrkdwns

            # bold
            s2 = re.sub(r"\*(.+)\*", r"<b>\1</b>", s2)

            # italic
            s2 = re.sub(r"\b_(.+)_\b", r"<i>\1</i>", s2)

            # code
            s2 = re.sub(
                r"`(.*)`",
                r'<s fontfamily="' + self._FONT_FAMILY_MONO_DEFAULT + r'">\1</s>',
                s2,
            )

            # indents
            s2 = re.sub(r"^>(.+)", r"<blockquote>\1</blockquote>", s2, 0, re.MULTILINE)

            s2 = s2.replace("</blockquote><br>", "</blockquote>")

            # EOF
            s2 = s2.replace("\n", "<br>")

        return s2

    def _format_datetime_str(self, dt):
        """returns formated datetime string for given dt using locale"""
        return format_datetime(dt, format="short", locale=self._my_locale)

    def _get_datetime_formatted_str(self, ts):
        """return given timestamp as formated datetime string using locale"""
        dt = self._get_datetime_from_ts(ts)
        return format_datetime(dt, format="short", locale=self._my_locale)

    def _get_time_formatted_str(self, ts):
        """return given timestamp as formated datetime string using locale"""
        dt = self._get_datetime_from_ts(ts)
        return format_time(dt, format="short", locale=self._my_locale)

    def _get_datetime_from_ts(self, ts):
        """returns datetime object of a unix timestamp with local timezone"""
        dt = datetime.fromtimestamp(float(ts), pytz.UTC)
        return dt.astimezone(self._my_tz)

    def _parse_message_and_write_to_pdf(self, document, msg, margin_left, last_user_id):
        """parse a message and write it to the PDF"""

        if "user" in msg:
            user_id = msg["user"]
            is_bot = False
            if user_id in self._user_names:
                user_name = self._user_names[user_id]
            else:
                user_name = f"unknown_user_{user_id}"

        elif "bot_id" in msg:
            user_id = msg["bot_id"]
            is_bot = True
            if "username" in msg:
                user_name = self._transform_encoding(msg["username"])
            elif user_id in self._bot_names:
                user_name = self._bot_names[user_id]
            else:
                user_name = f"unknown_bot_{user_id}"

        elif "subtype" in msg and msg["subtype"] == "file_comment":
            if "user" in msg["comment"]:
                user_id = msg["comment"]["user"]
                is_bot = False
                if user_id in self._user_names:
                    user_name = self._user_names[user_id]
                else:
                    user_name = f"unknown_user_{user_id}"
            else:
                user_name = None

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
                    self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL, style="B"
                )
                document.write(self._LINE_HEIGHT_DEFAULT, user_name + " ")
                document.set_font(self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_SMALL)
                if is_bot:
                    document.set_text_color(100, 100, 100)
                    document.write(self._LINE_HEIGHT_DEFAULT, "App ")
                    document.set_text_color(0)
                datetime_str = self._get_time_formatted_str(msg["ts"])
                document.write(self._LINE_HEIGHT_DEFAULT, datetime_str)
                document.ln()

            if "text" in msg and len(msg["text"]) > 0:
                text = msg["text"]
                if self._add_debug_info:
                    debug_text = (
                        f' [<s fontfamily="'
                        f'{self._FONT_FAMILY_MONO_DEFAULT}" size="8">'
                        f'{msg["ts"]}]</s>'
                    )
                else:
                    debug_text = ""
                document.set_font(
                    self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL
                )
                text_html = self._transform_text(
                    text, msg["mrkdwn"] if "mrkdwn" in msg else True
                )
                document.write_html(self._LINE_HEIGHT_DEFAULT, text_html + debug_text)
                document.ln()

            if "reactions" in msg:
                # draw reactions
                for reaction in msg["reactions"]:
                    document.set_left_margin(margin_left + self._TAB_WIDTH)
                    document.set_x(margin_left + self._TAB_WIDTH)
                    document.set_font(
                        self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL
                    )
                    document.write_html(
                        self._LINE_HEIGHT_DEFAULT,
                        (
                            "["
                            + reaction["name"]
                            + "] ("
                            + str(reaction["count"])
                            + "):"
                        ),
                    )
                    document.ln()

                    # convert user IDs to names
                    users_with_names = list()
                    for user in reaction["users"]:
                        if user in self._user_names:
                            user_name = self._user_names[user]
                        else:
                            user_name = "unknown_user_" + user

                        users_with_names.append("<b>" + user_name + "</b>")

                    document.set_left_margin(
                        margin_left + self._TAB_WIDTH + self._TAB_WIDTH
                    )
                    document.set_x(margin_left + self._TAB_WIDTH + self._TAB_WIDTH)
                    document.write_html(
                        self._LINE_HEIGHT_DEFAULT, ", ".join(users_with_names)
                    )
                    document.ln()

                document.ln(self._LINE_HEIGHT_SMALL)

            if "files" in msg:
                # draw files
                document.set_left_margin(margin_left + self._TAB_WIDTH)
                document.set_x(margin_left + self._TAB_WIDTH)

                for file in msg["files"]:
                    text = (
                        "["
                        + file["pretty_type"]
                        + " file: <b>"
                        + file["name"]
                        + "</b>"
                        + "]"
                    )
                    document.set_font(
                        self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL
                    )
                    document.write_html(self._LINE_HEIGHT_DEFAULT, text)
                    document.ln()

                    if "preview" in file:
                        text = file["preview"]
                        # remove document tag if any
                        match = re.match(r"<document>(.+)<\/document>", text)
                        if match is not None:
                            text = match.group(1)
                        # replace <p> with <br>
                        text = re.sub(r"<p>(.+)<\/p>", r"\1<br>", text)
                        # replace \r\n with <br>
                        text = re.sub(r"\n|\r\n", r"<br>", text)
                        # output
                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL
                        )
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
                            self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL
                        )
                        document.write_html(
                            self._LINE_HEIGHT_DEFAULT,
                            self._transform_text(
                                attach["pretext"], "pretext" in mrkdwn_in
                            ),
                        )
                        document.set_left_margin(margin_left + self._TAB_WIDTH)
                        document.set_x(margin_left + self._TAB_WIDTH)
                        document.ln()

                    document.ln(self._LINE_HEIGHT_SMALL)

                    if "author_name" in attach:
                        document.set_font(
                            self._FONT_FAMILY_DEFAULT,
                            size=self._FONT_SIZE_LARGE,
                            style="B",
                        )
                        document.write(
                            self._LINE_HEIGHT_DEFAULT,
                            self._transform_text(attach["author_name"]),
                        )
                        document.ln()

                    if "title" in attach:
                        title_text = self._transform_text(
                            attach["title"], "title" in mrkdwn_in
                        )

                        # add link to title if defined
                        if "title_link" in attach:
                            title_text = (
                                '<a href="'
                                + attach["title_link"]
                                + '">'
                                + title_text
                                + "</a>"
                            )

                        # add bold formatting to title
                        title_text = "<b>" + title_text + "</b>"

                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL
                        )
                        document.write_html(self._LINE_HEIGHT_DEFAULT, title_text)
                        document.ln()

                    if "text" in attach:
                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL
                        )
                        document.write_html(
                            self._LINE_HEIGHT_DEFAULT,
                            self._transform_text(attach["text"], "text" in mrkdwn_in),
                        )
                        document.ln()

                    if "fields" in attach:
                        for field in attach["fields"]:
                            document.set_font(
                                self._FONT_FAMILY_DEFAULT,
                                size=self._FONT_SIZE_NORMAL,
                                style="B",
                            )
                            document.write(
                                self._LINE_HEIGHT_DEFAULT,
                                self._transform_text(field["title"]),
                            )
                            document.ln()
                            document.set_font(
                                self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL
                            )
                            document.write_html(
                                self._LINE_HEIGHT_DEFAULT,
                                self._transform_text(
                                    field["value"], "fields" in mrkdwn_in
                                ),
                            )
                            document.ln()

                    if "footer" in attach:
                        if "ts" in attach:
                            text = (
                                self._transform_text(attach["footer"])
                                + "|"
                                + self._get_datetime_formatted_str(attach["ts"])
                            )
                        else:
                            text = self._transform_text(attach["footer"])

                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_SMALL
                        )
                        document.write(self._LINE_HEIGHT_DEFAULT, text)
                        document.ln()

                    if "image_url" in attach:
                        image_url_html = (
                            '<a href="' + attach["image_url"] + '">[Image]</a>'
                        )
                        document.set_font(
                            self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL
                        )
                        document.write_html(self._LINE_HEIGHT_DEFAULT, image_url_html)
                        document.ln()

                    # action attachments
                    if "actions" in attach:
                        for action in attach["actions"]:
                            document.set_font(
                                self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_SMALL
                            )
                            document.write_html(
                                self._LINE_HEIGHT_DEFAULT,
                                ("[" + self._transform_text(action["text"]) + "] "),
                            )

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
                            self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL
                        )
                        document.write_html(
                            self._LINE_HEIGHT_DEFAULT,
                            self._transform_text(
                                layout_block["text"]["text"],
                                layout_block["text"]["type"] == "mrkdwn",
                            ),
                        )
                        document.ln()

                        if "fields" in layout_block:
                            for field in layout_block["fields"]:
                                document.set_font(
                                    self._FONT_FAMILY_DEFAULT,
                                    size=self._FONT_SIZE_NORMAL,
                                )
                                document.write_html(
                                    self._LINE_HEIGHT_DEFAULT,
                                    self._transform_text(
                                        field["text"], field["type"] == "mrkdwn"
                                    ),
                                )
                                document.ln()

                document.ln(self._LINE_HEIGHT_SMALL)

        else:
            user_id = None
            print(f"WARN: Can not process message with ts {msg['ts']}")
            document.write(self._LINE_HEIGHT_DEFAULT, "[Can not process this message]")
            document.ln()

        return user_id

    def _write_messages_to_pdf(self, document, messages, threads):
        """writes messages with their threads to the PDF document"""
        last_user_id = None
        last_dt = None
        last_page = None

        if len(messages) > 0:
            messages = sorted(messages, key=lambda k: k["ts"])
            for msg in messages:

                msg_dt = self._get_datetime_from_ts(msg["ts"])

                # repeat user name for if last post from same user is older
                if last_dt is not None:
                    dt_delta = msg_dt - last_dt
                    minutes_delta = dt_delta / timedelta(minutes=1)
                    if minutes_delta > 30:
                        last_user_id = None

                # write day seperator if needed
                if last_dt is None or msg_dt.date() != last_dt.date():
                    document.ln(self._LINE_HEIGHT_SMALL)
                    document.ln(self._LINE_HEIGHT_SMALL)
                    document.set_font(
                        self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL
                    )

                    # draw divider line for next day
                    page_width = document.fw - 2 * self._MARGIN_LEFT
                    x1 = self._MARGIN_LEFT
                    x2 = x1 + page_width
                    y1 = document.get_y() + 3
                    document.line(x1, y1, x2, y1)

                    # stamp date on divider
                    date_text = format_date(
                        msg_dt, format="full", locale=self._my_locale
                    )
                    text_width = document.get_string_width(date_text)
                    x3 = (x2 - x1) / 2 + x1
                    x4 = x3 - (text_width / 2)
                    border_x = 3
                    document.set_fill_color(255, 255, 255)
                    document.set_x(x4 - border_x)
                    document.cell(
                        text_width + 2 * border_x,
                        self._LINE_HEIGHT_DEFAULT,
                        date_text,
                        0,
                        0,
                        "C",
                        True,
                    )

                    document.ln()
                    last_user_id = None  # repeat user name for new day

                # repeat user name for new page
                if last_page != document.page_no():
                    last_user_id = None
                    last_page = document.page_no()

                last_user_id = self._parse_message_and_write_to_pdf(
                    document, msg, self._MARGIN_LEFT, last_user_id
                )
                if "thread_ts" in msg and msg["thread_ts"] == msg["ts"]:
                    thread_ts = msg["thread_ts"]

                    if thread_ts in threads:
                        thread_messages = threads[thread_ts]
                        last_user_id = None
                        thread_messages = sorted(thread_messages, key=lambda k: k["ts"])
                        for thread_msg in thread_messages:
                            if thread_msg["ts"] != thread_msg["thread_ts"]:
                                last_user_id = self._parse_message_and_write_to_pdf(
                                    document,
                                    thread_msg,
                                    self._MARGIN_LEFT + self._TAB_WIDTH,
                                    last_user_id,
                                )

                    last_user_id = None

                last_dt = msg_dt
        else:
            document.set_font(self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL)
            document.ln()
            document.write(self._LINE_HEIGHT_DEFAULT, "This channel is empty", "I")

    def run(
        self,
        channel_inputs,
        dest_path=None,
        oldest=None,
        latest=None,
        page_orientation="portrait",
        page_format="a4",
        max_messages=None,
        write_raw_data=False,
    ):
        """export all message from a channel and store them in a PDF

        Args:
            channel_inputs: list of names and/or IDs of channels
            to retrieve messages from

            dest_path: path to write output files to. Will use current path if None

            oldest: oldest message to fetch in UNIX epoch
            latest: latest message to fetch in UNIX epoch

            page_orientation: orientation of pages  as defined in FPDF class,

            page_format: format of pages, see as defined in FPDF class

            max_messages: maximum number of messages to retrieve

            write_raw_data: will safe data received from API to files if true

        Returns:
            dict with full details of the export run
        """
        # set defaults
        success = False

        # input validation
        if max_messages is not None:
            if not isinstance(max_messages, int):
                raise TypeError("max_messages must be of type int")
        else:
            max_messages = self._MAX_MESSAGES_PER_CHANNEL

        if oldest is not None:
            if not isinstance(oldest, datetime):
                raise TypeError("oldest must be a datetime")
            else:
                oldest = self._my_tz.localize(oldest)

        if latest is not None:
            if not isinstance(latest, datetime):
                raise TypeError("latest must be a datetime")
            else:
                latest = self._my_tz.localize(latest)

        if oldest is not None and latest is not None and oldest > latest:
            raise RuntimeError("ERROR: oldest has to be before latest")

        if oldest is not None or latest is not None:
            text = "Fetching messages"
            if oldest is not None:
                text += f" after {self._format_datetime_str(oldest)}"
                if latest is not None:
                    text += " and"

            if latest is not None:
                text += f" before {self._format_datetime_str(latest)}"
            print(text)

        if type(channel_inputs) is not list:
            raise TypeError("channel_inputs must be of type list")

        # set destination path as current dir if not set
        # or check if given path exists
        if dest_path is None:
            dest_path = os.path.dirname(
                os.path.abspath(inspect.getfile(inspect.currentframe()))
            )
        else:
            if not isinstance(dest_path, str):
                raise TypeError("dest_path must be of type str")
            elif not os.path.isdir(dest_path):
                raise RuntimeError(
                    f"ERROR: give destination path does not exist: {dest_path}"
                )

        print(f"Writing output to: {dest_path}")

        if not isinstance(page_orientation, str):
            raise TypeError("page_orientation must be of type str")
        else:
            print(f"Page orientation: {page_orientation.title()}")

        if not isinstance(page_format, str):
            raise TypeError("page_format must be of type str")
        else:
            print(f"Page format: {page_format.title()}")

        if write_raw_data is not None and not isinstance(write_raw_data, bool):
            raise TypeError("write_raw_data must be of type bool")

        # prepare to process channels
        team_name = self._workspace_info["team"]
        response = {"ok": success, "channels": dict()}
        channel_count = 0
        success = True

        # process each channel
        for channel_input in channel_inputs:
            success_channel = False
            channel_count += 1
            print()
            if channel_input.upper() in self._channel_names:
                channel_id = channel_input.upper()
            else:
                # flip channel_names since channel names are unique
                channel_names_ids = {v: k for k, v in self._channel_names.items()}
                if channel_input.lower() not in channel_names_ids:
                    print(
                        f"({channel_count}/{len(channel_inputs)}) "
                        "ERROR: Unknown channel '"
                        f"{channel_input}' on {team_name}"
                    )
                    continue
                else:
                    channel_id = channel_names_ids[channel_input.lower()]

            channel_name = self._channel_names[channel_id]
            filename_base = os.path.join(
                dest_path, re.sub(r"[^\w\-_\.]", "_", team_name)
            )
            filename_base_channel = filename_base + "_" + channel_name

            # fetch messages
            # if we have a client fetch data from Slack
            if self._client is not None:
                if len(channel_inputs) > 1:
                    text = f"({channel_count}/{len(channel_inputs)}) "
                else:
                    text = ""
                text += "Retrieving messages from " + f"{team_name} / {channel_name}"

                print(text + " ...")
                messages = self._fetch_messages_from_channel(
                    channel_id, max_messages, oldest, latest
                )
                threads = self._fetch_threads_from_messages(
                    channel_id, messages, max_messages, oldest, latest
                )
                self._bot_names = self._fetch_bot_names_for_messages(messages, threads)

                if write_raw_data:
                    # write raw data received from Slack API to file
                    self._write_array_to_json_file(
                        self._user_names, filename_base + "_users"
                    )
                    self._write_array_to_json_file(
                        self._bot_names, filename_base + "_bots"
                    )
                    self._write_array_to_json_file(
                        self._channel_names, filename_base + "_channels"
                    )
                    self._write_array_to_json_file(
                        self._usergroup_names, filename_base + "_usergroups"
                    )
                    self._write_array_to_json_file(
                        messages, filename_base_channel + "_messages"
                    )
                    if len(threads) > 0:
                        self._write_array_to_json_file(
                            threads, filename_base_channel + "_threads"
                        )
            else:
                # if we don't have a client we will try to fetch from a file
                # this is used for testing
                messages = self._read_array_from_json_file(
                    filename_base_channel + "_messages"
                )
                threads = self._read_array_from_json_file(
                    filename=filename_base_channel + "_threads", quiet=True
                )

            # create PDF
            document = MyFPDF(page_orientation, self._PAGE_UNITS_DEFAULT, page_format)

            # add all fonts to support unicode
            document.add_font(
                self._FONT_FAMILY_DEFAULT,
                style="",
                fname="NotoSans-Regular.ttf",
                uni=True,
            )
            document.add_font(
                self._FONT_FAMILY_DEFAULT,
                style="B",
                fname="NotoSans-Bold.ttf",
                uni=True,
            )
            document.add_font(
                self._FONT_FAMILY_DEFAULT,
                style="I",
                fname="NotoSans-Italic.ttf",
                uni=True,
            )
            document.add_font(
                self._FONT_FAMILY_DEFAULT,
                style="BI",
                fname="NotoSans-BoldItalic.ttf",
                uni=True,
            )
            document.add_font(
                self._FONT_FAMILY_MONO_DEFAULT,
                style="",
                fname="NotoSansMono-Regular.ttf",
                uni=True,
            )
            document.add_font(
                self._FONT_FAMILY_MONO_DEFAULT,
                style="B",
                fname="NotoSansMono-Bold.ttf",
                uni=True,
            )
            document.alias_nb_pages()
            document.add_page()

            # compile all values
            workspace_name = self._workspace_info["team"]
            channel_name = self._channel_names[channel_id]
            creation_date = datetime.now(tz=self._my_tz)
            creation_datetime_str = self._format_datetime_str(creation_date)

            # count all messages including threads
            message_count = len(messages)
            if len(threads) > 0:
                for thread_ts, thread_messages in threads.items():
                    message_count += len(thread_messages) - 1

            if message_count > 0:
                # find start and end date based on messages
                ts_extract = [d["ts"] for d in messages]
                ts_min = min(float(s) for s in ts_extract)
                ts_max = max(float(s) for s in ts_extract)

                start_date = self._get_datetime_from_ts(ts_min)
                start_date_str = self._format_datetime_str(start_date)
                end_date = self._get_datetime_from_ts(ts_max)
                end_date_str = self._format_datetime_str(end_date)
            else:
                start_date = None
                start_date_str = ""
                end_date = None
                end_date_str = ""

            # set variables for title, header, footer
            title = workspace_name + " / " + channel_name
            sub_title = "Slack channel export"
            page_title = title

            # set properties for document info
            document.set_author(self._author)
            document.set_creator(f"Channel Export v{__version__}")
            document.set_title(title)
            # document.set_creation_date(creation_date)
            document.set_subject(sub_title)
            document.page_title = page_title

            # write title on first page
            document.set_font(
                self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_LARGE, style="B"
            )
            document.cell(0, 0, title, 0, 1, "C")
            document.ln(self._LINE_HEIGHT_DEFAULT)

            document.set_font(
                self._FONT_FAMILY_DEFAULT, size=self._FONT_SIZE_NORMAL, style="B"
            )
            document.cell(0, 0, sub_title, 0, 1, "C")
            document.ln(self._LINE_HEIGHT_DEFAULT)

            # write info block after title
            thread_count = len(threads.keys()) if len(threads) > 0 else 0
            export_infos = {
                "Slack workspace": workspace_name,
                "Channel": channel_name,
                "Exported at": creation_datetime_str,
                "Exported by": self._author,
                "Start date": start_date_str,
                "End date": end_date_str,
                "Timezone": self._my_tz,
                "Locale": f"{self._my_locale.get_display_name()}",
                "Messages": format_number(message_count, locale=self._my_locale),
                "Threads": format_number(thread_count, locale=self._my_locale),
                "Pages": "{nb}",
            }
            document.write_info_table(export_infos)
            document.add_page()

            # write messages to PDF
            self._write_messages_to_pdf(document, messages, threads)

            # store PDF
            filename_pdf = filename_base_channel + ".pdf"
            print("Writing PDF file: " + filename_pdf)
            try:
                document.output(filename_pdf)
                success_channel = True
            except Exception as e:
                print("ERROR: Failed to write PDF file: ", e)

            # compile response dict
            response["channels"][channel_id] = {
                "ok": success_channel,
                "channel_id": channel_id,
                "channel_name": channel_name,
                "filename_pdf": filename_pdf,
                "filename_base_channel": filename_base_channel,
                "dest_path": dest_path,
                "page_format": page_format,
                "page_orientation": page_orientation,
                "max_messages": max_messages,
                "messages_total": max_messages,
                "export_infos": export_infos,
                "message_count": message_count,
                "thread_count": thread_count,
                "creation_date": creation_date,
                "start_date": start_date,
                "end_date": end_date,
                "timezone": self._my_tz,
                "locale": self._my_locale,
            }
            success = success and success_channel

        response["ok"] = success
        return response
