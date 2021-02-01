import re

from .helpers import transform_encoding


class MessageTransformer:
    """parsing and transforming Slack messages"""

    def __init__(self, slack_service, locale_helper, font_family_mono_default) -> None:
        self._slack_service = slack_service
        self._locale_helper = locale_helper
        self._font_family_mono_default = font_family_mono_default

    def transform_text(self, text, use_mrkdwn=False):
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
            obj_id = parts[0]

            make_bold = True
            if id_chars == "@U" or id_chars == "@W":
                # match is a user ID
                if obj_id in self._slack_service.user_names():
                    replacement = "@" + self._slack_service.user_names()[obj_id]
                else:
                    replacement = f"@user_{obj_id}"

            elif id_chars == "#C":
                # match is a channel ID
                if obj_id in self._slack_service.channel_names():
                    replacement = "#" + self._slack_service.channel_names()[obj_id]
                else:
                    replacement = f"#channel_{obj_id}"

            elif match[0:9] == "!subteam^":
                # match is a user group ID
                match2 = re.match(r"!subteam\^(S[A-Z0-9]+)", match)
                if match2 is not None and len(match2.groups()) == 1:
                    usergroup_id = match2.group(1)
                    if usergroup_id in self._slack_service.usergroup_names():
                        usergroup_name = self._slack_service.usergroup_names()[
                            usergroup_id
                        ]
                    else:
                        usergroup_name = f"usergroup_{usergroup_id}"
                else:
                    usergroup_name = "usergroup_unknown"
                replacement = "@" + usergroup_name

            elif match[0:1] == "!":
                # match is a special mention
                if obj_id == "here":
                    replacement = "@here"

                elif obj_id == "channel":
                    replacement = "@channel"

                elif obj_id == "everyone":
                    replacement = "@everyone"

                elif match[0:5] == "!date":
                    make_bold = False
                    date_parts = match.split("^")
                    if len(date_parts) > 1:
                        replacement = self._locale_helper.get_datetime_formatted_str(
                            date_parts[1]
                        )
                    else:
                        replacement = "(failed to parse date)"

                else:
                    replacement = f"@special_{obj_id}"

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
        s2 = transform_encoding(text)

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
                r'<s fontfamily="' + self._font_family_mono_default + r'">\1</s>',
                s2,
            )

            # indents
            s2 = re.sub(r"^>(.+)", r"<blockquote>\1</blockquote>", s2, 0, re.MULTILINE)

            s2 = s2.replace("</blockquote><br>", "</blockquote>")

            # EOF
            s2 = s2.replace("\n", "<br>")

        return s2
