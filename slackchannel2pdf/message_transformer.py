"""Slack message transformers for slackchannel2pdf."""

import re

from .helpers import transform_encoding
from .locales import LocaleHelper
from .slack_service import SlackService


class MessageTransformer:
    """A class for parsing and transforming Slack messages."""

    def __init__(
        self,
        slack_service: SlackService,
        locale_helper: LocaleHelper,
        font_family_mono_default: str,
    ) -> None:
        self._slack_service = slack_service
        self._locale_helper = locale_helper
        self._font_family_mono_default = font_family_mono_default

    def transform_text(self, text: str, use_mrkdwn: bool = False) -> str:
        """Transform mrkdwn text into HTML text for PDF output.

        Main method to resolve all mrkdwn, e.g. <C12345678>, <!here>, *bold*
        Will resolve channel and user IDs to their names if possible
        Returns string with rudimentary HTML for formatting and links

        Attr:
            text: text string to be transformed
            use_mrkdwn: will transform mrkdwn if set to true

        Returns:
            transformed text string with HTML formatting
        """

        # pass 1 - adjust encoding to latin-1 and transform HTML entities
        result = transform_encoding(text)

        # if requested try to transform mrkdwn in text
        if use_mrkdwn:
            # pass 2 - transform mrkdwns with brackets
            result = re.sub(r"<(.*?)>", self._replace_mrkdwn_in_text, result)

            # pass 3 - transform formatting mrkdwns

            # bold
            result = re.sub(r"\*(.+)\*", r"<b>\1</b>", result)
            # italic
            result = re.sub(r"\b_(.+)_\b", r"<i>\1</i>", result)
            # code
            result = re.sub(
                r"`(.*)`",
                r'<s fontfamily="' + self._font_family_mono_default + r'">\1</s>',
                result,
            )
            # indents
            result = re.sub(
                r"^>(.+)", r"<blockquote>\1</blockquote>", result, 0, re.MULTILINE
            )
            result = result.replace("</blockquote><br>", "</blockquote>")
            # EOF
            result = result.replace("\n", "<br>")

        return result

    def _replace_mrkdwn_in_text(self, match_obj: re.Match) -> str:
        """inline function returns replacement string for re.sub

        This function does the actual resolving of IDs and mrkdwn key words
        """
        match = match_obj.group(1)

        id_chars = match[0:2]
        id_raw = match[1 : len(match)]
        parts = id_raw.split("|", 1)
        obj_id = parts[0]

        make_bold = True
        if id_chars in {"@U", "@W"}:
            result = self._process_user_id(obj_id)

        elif id_chars == "#C":
            result = self._process_channel_id(obj_id)

        elif match[0:9] == "!subteam^":
            result = self._process_user_group_id(match)

        elif match[0:1] == "!":
            make_bold, result = self._process_special_mention(match, obj_id)

        else:
            make_bold, result = self._process_url(match)

        if make_bold:
            result = f"<b>{result}</b>"

        return result

    def _process_user_id(self, obj_id):
        if obj_id in self._slack_service.user_names():
            return "@" + self._slack_service.user_names()[obj_id]

        return f"@user_{obj_id}"

    def _process_channel_id(self, obj_id):
        if obj_id in self._slack_service.channel_names():
            return "#" + self._slack_service.channel_names()[obj_id]

        return f"#channel_{obj_id}"

    def _process_user_group_id(self, match):
        match2 = re.match(r"!subteam\^(S[A-Z0-9]+)", match)
        if match2 is not None and len(match2.groups()) == 1:
            usergroup_id = match2.group(1)
            if usergroup_id in self._slack_service.usergroup_names():
                usergroup_name = self._slack_service.usergroup_names()[usergroup_id]
            else:
                usergroup_name = f"usergroup_{usergroup_id}"
        else:
            usergroup_name = "usergroup_unknown"
        return "@" + usergroup_name

    def _process_special_mention(self, match, obj_id):
        make_bold = True
        if obj_id == "here":
            result = "@here"

        elif obj_id == "channel":
            result = "@channel"

        elif obj_id == "everyone":
            result = "@everyone"

        elif match[0:5] == "!date":
            make_bold = False
            date_parts = match.split("^")
            if len(date_parts) > 1:
                result = self._locale_helper.get_datetime_formatted_str(date_parts[1])
            else:
                result = "(failed to parse date)"

        else:
            result = f"@special_{obj_id}"

        return make_bold, result

    def _process_url(self, match):
        link_parts = match.split("|")
        if len(link_parts) == 2:
            url = link_parts[0]
            text = link_parts[1]
        else:
            url = match
            text = match

        make_bold = False
        result = f'<a href="{url}">{text}</a>'
        return make_bold, result
