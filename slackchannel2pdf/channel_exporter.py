from datetime import datetime, timedelta
import inspect
import os
import re

from babel.numbers import format_number

from . import __version__
from . import settings
from .my_fpdf import MyFPDF
from .helpers import (
    transform_encoding,
    LocaleHelper,
    read_array_from_json_file,
    write_array_to_json_file,
)
from .slack_service import SlackService
from .message_transformer import MessageTransformer


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

    def __init__(self, slack_token, my_tz=None, my_locale=None, add_debug_info=False):
        """
        Args:
            slack_token: OAuth token to be used for all calls to the Slack API
                "TEST" can be provided to start test mode
            my_tz: override system's timezone (pytz.BaseTzInfo object)
            my_locale: override system's locale (locale string, e.g. 'de_DE')
            add_debug_info: wether to add debug info to message output

        """
        self._bot_names = dict()
        if slack_token is None:
            raise ValueError("slack_token can not be null")

        self._slack_service = SlackService(slack_token)

        # output welcome message and inform about current parameters
        print()
        print("Welcome " + self._slack_service.author)

        # set locale & timezone
        author_info = self._slack_service.author_info()
        self._locale_helper = LocaleHelper(my_locale, my_tz, author_info)
        self._locale_helper.print_locale()
        self._locale_helper.print_timezone()
        self._transformer = MessageTransformer(
            slack_service=self._slack_service,
            locale_helper=self._locale_helper,
            font_family_mono_default=settings.FONT_FAMILY_MONO_DEFAULT,
        )

        # validate add_debug_info
        if not isinstance(add_debug_info, bool):
            raise ValueError("add_debug_info must be bool")
        self._add_debug_info = add_debug_info
        if add_debug_info:
            print("Adding DEBUG info to PDF")

    def _parse_message_and_write_to_pdf(self, document, msg, margin_left, last_user_id):
        """parse a message and write it to the PDF"""

        if "user" in msg:
            user_id = msg["user"]
            is_bot = False
            if user_id in self._slack_service.user_names():
                user_name = self._slack_service.user_names()[user_id]
            else:
                user_name = f"unknown_user_{user_id}"

        elif "bot_id" in msg:
            user_id = msg["bot_id"]
            is_bot = True
            if "username" in msg:
                user_name = transform_encoding(msg["username"])
            elif user_id in self._bot_names:
                user_name = self._bot_names[user_id]
            else:
                user_name = f"unknown_bot_{user_id}"

        elif "subtype" in msg and msg["subtype"] == "file_comment":
            is_bot = False
            if "user" in msg["comment"]:
                user_id = msg["comment"]["user"]
                if user_id in self._slack_service.user_names():
                    user_name = self._slack_service.user_names()[user_id]
                else:
                    user_name = f"unknown_user_{user_id}"
            else:
                user_id = None
                user_name = None

        else:
            is_bot = False
            user_id = None
            user_name = None

        if user_name is not None:
            # start again on the left border
            document.set_left_margin(margin_left)
            document.set_x(margin_left)

            if last_user_id != user_id:
                # write user name and date only when user switches
                document.ln(settings.LINE_HEIGHT_SMALL)
                document.set_font(
                    settings.FONT_FAMILY_DEFAULT,
                    size=settings.FONT_SIZE_NORMAL,
                    style="B",
                )
                document.write(settings.LINE_HEIGHT_DEFAULT, user_name + " ")
                document.set_font(
                    settings.FONT_FAMILY_DEFAULT, size=settings.FONT_SIZE_SMALL
                )
                if is_bot:
                    document.set_text_color(100, 100, 100)
                    document.write(settings.LINE_HEIGHT_DEFAULT, "App ")
                    document.set_text_color(0)
                datetime_str = self._locale_helper.get_time_formatted_str(msg["ts"])
                document.write(settings.LINE_HEIGHT_DEFAULT, datetime_str)
                document.ln()

            if "text" in msg and len(msg["text"]) > 0:
                text = msg["text"]
                if self._add_debug_info:
                    debug_text = (
                        f' [<s fontfamily="'
                        f'{settings.FONT_FAMILY_MONO_DEFAULT}" size="8">'
                        f'{msg["ts"]}]</s>'
                    )
                else:
                    debug_text = ""
                document.set_font(
                    settings.FONT_FAMILY_DEFAULT, size=settings.FONT_SIZE_NORMAL
                )
                text_html = self._transformer.transform_text(
                    text, msg["mrkdwn"] if "mrkdwn" in msg else True
                )
                document.write_html(
                    settings.LINE_HEIGHT_DEFAULT, text_html + debug_text
                )
                document.ln()

            if "reactions" in msg:
                # draw reactions
                for reaction in msg["reactions"]:
                    document.set_left_margin(margin_left + settings.TAB_WIDTH)
                    document.set_x(margin_left + settings.TAB_WIDTH)
                    document.set_font(
                        settings.FONT_FAMILY_DEFAULT, size=settings.FONT_SIZE_NORMAL
                    )
                    document.write_html(
                        settings.LINE_HEIGHT_DEFAULT,
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
                        if user in self._slack_service.user_names():
                            user_name = self._slack_service.user_names()[user]
                        else:
                            user_name = "unknown_user_" + user

                        users_with_names.append("<b>" + user_name + "</b>")

                    document.set_left_margin(
                        margin_left + settings.TAB_WIDTH + settings.TAB_WIDTH
                    )
                    document.set_x(
                        margin_left + settings.TAB_WIDTH + settings.TAB_WIDTH
                    )
                    document.write_html(
                        settings.LINE_HEIGHT_DEFAULT, ", ".join(users_with_names)
                    )
                    document.ln()

                document.ln(settings.LINE_HEIGHT_SMALL)

            if "files" in msg:
                # draw files
                document.set_left_margin(margin_left + settings.TAB_WIDTH)
                document.set_x(margin_left + settings.TAB_WIDTH)

                for file in msg["files"]:
                    file_type = file.get("pretty_type", "")
                    file_name = file.get("name", "")
                    text = "[" + file_type + " file: <b>" + file_name + "</b>" + "]"
                    document.set_font(
                        settings.FONT_FAMILY_DEFAULT, size=settings.FONT_SIZE_NORMAL
                    )
                    document.write_html(settings.LINE_HEIGHT_DEFAULT, text)
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
                            settings.FONT_FAMILY_DEFAULT,
                            size=settings.FONT_SIZE_NORMAL,
                        )
                        document.write_html(settings.LINE_HEIGHT_DEFAULT, text)
                        document.ln()

            if "attachments" in msg:
                # draw attachments
                document.set_left_margin(margin_left + settings.TAB_WIDTH)
                document.set_x(margin_left + settings.TAB_WIDTH)

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
                            settings.FONT_FAMILY_DEFAULT,
                            size=settings.FONT_SIZE_NORMAL,
                        )
                        document.write_html(
                            settings.LINE_HEIGHT_DEFAULT,
                            self._transformer.transform_text(
                                attach["pretext"], "pretext" in mrkdwn_in
                            ),
                        )
                        document.set_left_margin(margin_left + settings.TAB_WIDTH)
                        document.set_x(margin_left + settings.TAB_WIDTH)
                        document.ln()

                    document.ln(settings.LINE_HEIGHT_SMALL)

                    if "author_name" in attach:
                        document.set_font(
                            settings.FONT_FAMILY_DEFAULT,
                            size=settings.FONT_SIZE_LARGE,
                            style="B",
                        )
                        document.write(
                            settings.LINE_HEIGHT_DEFAULT,
                            self._transformer.transform_text(attach["author_name"]),
                        )
                        document.ln()

                    if "title" in attach:
                        title_text = self._transformer.transform_text(
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
                            settings.FONT_FAMILY_DEFAULT,
                            size=settings.FONT_SIZE_NORMAL,
                        )
                        document.write_html(settings.LINE_HEIGHT_DEFAULT, title_text)
                        document.ln()

                    if "text" in attach:
                        document.set_font(
                            settings.FONT_FAMILY_DEFAULT,
                            size=settings.FONT_SIZE_NORMAL,
                        )
                        document.write_html(
                            settings.LINE_HEIGHT_DEFAULT,
                            self._transformer.transform_text(
                                attach["text"], "text" in mrkdwn_in
                            ),
                        )
                        document.ln()

                    if "fields" in attach:
                        for field in attach["fields"]:
                            document.set_font(
                                settings.FONT_FAMILY_DEFAULT,
                                size=settings.FONT_SIZE_NORMAL,
                                style="B",
                            )
                            document.write(
                                settings.LINE_HEIGHT_DEFAULT,
                                self._transformer.transform_text(field["title"]),
                            )
                            document.ln()
                            document.set_font(
                                settings.FONT_FAMILY_DEFAULT,
                                size=settings.FONT_SIZE_NORMAL,
                            )
                            document.write_html(
                                settings.LINE_HEIGHT_DEFAULT,
                                self._transformer.transform_text(
                                    field["value"], "fields" in mrkdwn_in
                                ),
                            )
                            document.ln()

                    if "footer" in attach:
                        if "ts" in attach:
                            text = (
                                self._transformer.transform_text(attach["footer"])
                                + "|"
                                + self._locale_helper.get_datetime_formatted_str(
                                    attach["ts"]
                                )
                            )
                        else:
                            text = self._transformer.transform_text(attach["footer"])

                        document.set_font(
                            settings.FONT_FAMILY_DEFAULT,
                            size=settings.FONT_SIZE_SMALL,
                        )
                        document.write(settings.LINE_HEIGHT_DEFAULT, text)
                        document.ln()

                    if "image_url" in attach:
                        image_url_html = (
                            '<a href="' + attach["image_url"] + '">[Image]</a>'
                        )
                        document.set_font(
                            settings.FONT_FAMILY_DEFAULT,
                            size=settings.FONT_SIZE_NORMAL,
                        )
                        document.write_html(
                            settings.LINE_HEIGHT_DEFAULT, image_url_html
                        )
                        document.ln()

                    # action attachments
                    if "actions" in attach:
                        for action in attach["actions"]:
                            document.set_font(
                                settings.FONT_FAMILY_DEFAULT,
                                size=settings.FONT_SIZE_SMALL,
                            )
                            document.write_html(
                                settings.LINE_HEIGHT_DEFAULT,
                                (
                                    "["
                                    + self._transformer.transform_text(action["text"])
                                    + "] "
                                ),
                            )

                        document.ln()

                document.ln(settings.LINE_HEIGHT_SMALL)

            if "blocks" in msg:
                document.set_left_margin(margin_left + settings.TAB_WIDTH)
                document.set_x(margin_left + settings.TAB_WIDTH)

                for layout_block in msg["blocks"]:
                    block_type = layout_block["type"]
                    document.ln(settings.LINE_HEIGHT_SMALL)

                    # section layout blocks
                    if block_type == "section":
                        document.set_font(
                            settings.FONT_FAMILY_DEFAULT,
                            size=settings.FONT_SIZE_NORMAL,
                        )
                        document.write_html(
                            settings.LINE_HEIGHT_DEFAULT,
                            self._transformer.transform_text(
                                layout_block["text"]["text"],
                                layout_block["text"]["type"] == "mrkdwn",
                            ),
                        )
                        document.ln()

                        if "fields" in layout_block:
                            for field in layout_block["fields"]:
                                document.set_font(
                                    settings.FONT_FAMILY_DEFAULT,
                                    size=settings.FONT_SIZE_NORMAL,
                                )
                                document.write_html(
                                    settings.LINE_HEIGHT_DEFAULT,
                                    self._transformer.transform_text(
                                        field["text"], field["type"] == "mrkdwn"
                                    ),
                                )
                                document.ln()

                document.ln(settings.LINE_HEIGHT_SMALL)

        else:
            user_id = None
            print(f"WARN: Can not process message with ts {msg['ts']}")
            document.write(
                settings.LINE_HEIGHT_DEFAULT, "[Can not process this message]"
            )
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

                msg_dt = self._locale_helper.get_datetime_from_ts(msg["ts"])

                # repeat user name for if last post from same user is older
                if last_dt is not None:
                    dt_delta = msg_dt - last_dt
                    minutes_delta = dt_delta / timedelta(minutes=1)
                    if minutes_delta > settings.MINUTES_UNTIL_USERNAME_REPEATS:
                        last_user_id = None

                # write day seperator if needed
                if last_dt is None or msg_dt.date() != last_dt.date():
                    document.ln(settings.LINE_HEIGHT_SMALL)
                    document.ln(settings.LINE_HEIGHT_SMALL)
                    document.set_font(
                        settings.FONT_FAMILY_DEFAULT, size=settings.FONT_SIZE_NORMAL
                    )

                    # draw divider line for next day
                    page_width = document.fw - 2 * settings.MARGIN_LEFT
                    x1 = settings.MARGIN_LEFT
                    x2 = x1 + page_width
                    y1 = document.get_y() + 3
                    document.line(x1, y1, x2, y1)

                    # stamp date on divider
                    date_text = self._locale_helper.format_date_full_str(msg_dt)
                    text_width = document.get_string_width(date_text)
                    x3 = (x2 - x1) / 2 + x1
                    x4 = x3 - (text_width / 2)
                    border_x = 3
                    document.set_fill_color(255, 255, 255)
                    document.set_x(x4 - border_x)
                    document.cell(
                        text_width + 2 * border_x,
                        settings.LINE_HEIGHT_DEFAULT,
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
                    document, msg, settings.MARGIN_LEFT, last_user_id
                )
                if "thread_ts" in msg and msg["thread_ts"] == msg["ts"]:
                    thread_ts = msg["thread_ts"]

                    if thread_ts in threads:
                        thread_messages = threads[thread_ts]
                        last_user_id = None
                        last_dt = None
                        thread_messages = sorted(thread_messages, key=lambda k: k["ts"])
                        for thread_msg in thread_messages:
                            if thread_msg["ts"] != thread_msg["thread_ts"]:
                                # repeat user name for if last post from same user is older
                                msg_dt = self._locale_helper.get_datetime_from_ts(
                                    thread_msg["ts"]
                                )
                                if last_dt is not None:
                                    dt_delta = msg_dt - last_dt
                                    minutes_delta = dt_delta / timedelta(minutes=1)
                                    if (
                                        minutes_delta
                                        > settings.MINUTES_UNTIL_USERNAME_REPEATS
                                    ):
                                        last_user_id = None
                                last_dt = msg_dt
                                last_user_id = self._parse_message_and_write_to_pdf(
                                    document,
                                    thread_msg,
                                    settings.MARGIN_LEFT + settings.TAB_WIDTH,
                                    last_user_id,
                                )

                    last_user_id = None

                last_dt = msg_dt
        else:
            document.set_font(
                settings.FONT_FAMILY_DEFAULT, size=settings.FONT_SIZE_NORMAL
            )
            document.ln()
            document.write(settings.LINE_HEIGHT_DEFAULT, "This channel is empty", "I")

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
            max_messages = settings.MAX_MESSAGES_PER_CHANNEL

        if oldest is not None:
            if not isinstance(oldest, datetime):
                raise TypeError("oldest must be a datetime")
            oldest = self._locale_helper.timezone.localize(oldest)

        if latest is not None:
            if not isinstance(latest, datetime):
                raise TypeError("latest must be a datetime")
            latest = self._locale_helper.timezone.localize(latest)

        if oldest is not None and latest is not None and oldest > latest:
            raise RuntimeError("ERROR: oldest has to be before latest")

        if oldest is not None or latest is not None:
            text = "Fetching messages"
            if oldest is not None:
                text += f" after {self._locale_helper.format_datetime_str(oldest)}"
                if latest is not None:
                    text += " and"

            if latest is not None:
                text += f" before {self._locale_helper.format_datetime_str(latest)}"
            print(text)

        if not isinstance(channel_inputs, list):
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
            if not os.path.isdir(dest_path):
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
        team_name = self._slack_service.team
        response = {"ok": success, "channels": dict()}
        channel_count = 0
        success = True

        # process each channel
        for channel_input in channel_inputs:
            success_channel = False
            channel_count += 1
            print()
            if channel_input.upper() in self._slack_service.channel_names():
                channel_id = channel_input.upper()
            else:
                # flip channel_names since channel names are unique
                channel_names_ids = {
                    v: k for k, v in self._slack_service.channel_names().items()
                }
                if channel_input.lower() not in channel_names_ids:
                    print(
                        f"({channel_count}/{len(channel_inputs)}) "
                        "ERROR: Unknown channel '"
                        f"{channel_input}' on {team_name}"
                    )
                    continue
                else:
                    channel_id = channel_names_ids[channel_input.lower()]

            channel_name = self._slack_service.channel_names()[channel_id]
            filename_base = os.path.join(
                dest_path, re.sub(r"[^\w\-_\.]", "_", team_name)
            )
            filename_base_channel = filename_base + "_" + channel_name

            # fetch messages
            # if we have a client fetch data from Slack
            if not self._slack_service.is_test_mode:
                if len(channel_inputs) > 1:
                    text = f"({channel_count}/{len(channel_inputs)}) "
                else:
                    text = ""
                text += "Retrieving messages from " + f"{team_name} / {channel_name}"

                print(text + " ...")
                messages = self._slack_service.fetch_messages_from_channel(
                    channel_id, max_messages, oldest, latest
                )
                threads = self._slack_service.fetch_threads_from_messages(
                    channel_id, messages, max_messages, oldest, latest
                )
                self._bot_names = self._slack_service.fetch_bot_names_for_messages(
                    messages, threads
                )

                if write_raw_data:
                    # write raw data received from Slack API to file
                    write_array_to_json_file(
                        self._slack_service.user_names(), filename_base + "_users"
                    )
                    write_array_to_json_file(self._bot_names, filename_base + "_bots")
                    write_array_to_json_file(
                        self._slack_service.channel_names(), filename_base + "_channels"
                    )
                    write_array_to_json_file(
                        self._slack_service.user_names(), filename_base + "_usergroups"
                    )
                    write_array_to_json_file(
                        messages, filename_base_channel + "_messages"
                    )
                    if len(threads) > 0:
                        write_array_to_json_file(
                            threads, filename_base_channel + "_threads"
                        )
            else:
                # if we don't have a client we will try to fetch from a file
                # this is used for testing
                messages = read_array_from_json_file(
                    filename_base_channel + "_messages"
                )
                threads = read_array_from_json_file(
                    filename=filename_base_channel + "_threads", quiet=True
                )

            # create PDF
            document = MyFPDF(
                page_orientation, settings.PAGE_UNITS_DEFAULT, page_format
            )

            # add all fonts to support unicode
            document.add_font(
                settings.FONT_FAMILY_DEFAULT,
                style="",
                fname="NotoSans-Regular.ttf",
                uni=True,
            )
            document.add_font(
                settings.FONT_FAMILY_DEFAULT,
                style="B",
                fname="NotoSans-Bold.ttf",
                uni=True,
            )
            document.add_font(
                settings.FONT_FAMILY_DEFAULT,
                style="I",
                fname="NotoSans-Italic.ttf",
                uni=True,
            )
            document.add_font(
                settings.FONT_FAMILY_DEFAULT,
                style="BI",
                fname="NotoSans-BoldItalic.ttf",
                uni=True,
            )
            document.add_font(
                settings.FONT_FAMILY_MONO_DEFAULT,
                style="",
                fname="NotoSansMono-Regular.ttf",
                uni=True,
            )
            document.add_font(
                settings.FONT_FAMILY_MONO_DEFAULT,
                style="B",
                fname="NotoSansMono-Bold.ttf",
                uni=True,
            )
            document.alias_nb_pages()
            document.add_page()

            # compile all values
            creation_date = datetime.now(tz=self._locale_helper.timezone)
            creation_datetime_str = self._locale_helper.format_datetime_str(
                creation_date
            )

            # count all messages including threads
            message_count = len(messages)
            if len(threads) > 0:
                for _, thread_messages in threads.items():
                    message_count += len(thread_messages) - 1

            if message_count > 0:
                # find start and end date based on messages
                ts_extract = [d["ts"] for d in messages]
                ts_min = min(float(s) for s in ts_extract)
                ts_max = max(float(s) for s in ts_extract)

                start_date = self._locale_helper.get_datetime_from_ts(ts_min)
                start_date_str = self._locale_helper.format_datetime_str(start_date)
                end_date = self._locale_helper.get_datetime_from_ts(ts_max)
                end_date_str = self._locale_helper.format_datetime_str(end_date)
            else:
                start_date = None
                start_date_str = ""
                end_date = None
                end_date_str = ""

            # set variables for title, header, footer
            title = team_name + " / " + channel_name
            sub_title = "Slack channel export"
            page_title = title

            # set properties for document info
            document.set_author(self._slack_service.author)
            document.set_creator(f"Channel Export v{__version__}")
            document.set_title(title)
            # document.set_creation_date(creation_date)
            document.set_subject(sub_title)
            document.page_title = page_title

            # write title on first page
            document.set_font(
                settings.FONT_FAMILY_DEFAULT, size=settings.FONT_SIZE_LARGE, style="B"
            )
            document.cell(0, 0, title, 0, 1, "C")
            document.ln(settings.LINE_HEIGHT_DEFAULT)

            document.set_font(
                settings.FONT_FAMILY_DEFAULT,
                size=settings.FONT_SIZE_NORMAL,
                style="B",
            )
            document.cell(0, 0, sub_title, 0, 1, "C")
            document.ln(settings.LINE_HEIGHT_DEFAULT)

            # write info block after title
            thread_count = len(threads.keys()) if len(threads) > 0 else 0
            export_infos = {
                "Slack workspace": team_name,
                "Channel": channel_name,
                "Exported at": creation_datetime_str,
                "Exported by": self._slack_service.author,
                "Start date": start_date_str,
                "End date": end_date_str,
                "Timezone": self._locale_helper.timezone,
                "Locale": f"{self._locale_helper.locale.get_display_name()}",
                "Messages": format_number(
                    message_count, locale=self._locale_helper.locale
                ),
                "Threads": format_number(
                    thread_count, locale=self._locale_helper.locale
                ),
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
            except IOError as ex:
                print("ERROR: Failed to write PDF file: ", ex)

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
                "timezone": self._locale_helper.timezone,
                "locale": self._locale_helper.locale,
            }
            success = success and success_channel

        response["ok"] = success
        return response
