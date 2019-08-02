def _generate_emoji_map(self):
    """returns a dict of names to UTF-8 string for all known emojis"""
    map = dict()
    try:
        with open(self._FILE_EMOJIS, 'r', encoding="utf-8") as f:
            emojis = json.load(f)
        for emoji in emojis:
            if "short_name" in emoji:
                k = emoji["short_name"]
                cps = emoji["unified"].split("-")
                chars = ""
                for cp in cps:
                    chars += chr(int(cp, 16))
                map[k] = chars
        
    except Exception as ex:
        print("WARN: failed to load emojis", ex)
        map = []

    return map

def replace_emoji_name(matchObj):
    match = matchObj.group(1).lower()
    
    if match in self._emoji_map:
        replacement = ('<s fontfamily="' 
            + self._FONT_FAMILY_EMOJI_DEFAULT 
            + '">'
            + self._emoji_map[match]
            + '</s>')
    else:
        replacement = matchObj.group(0)

    return replacement

""" replacing in text_transform()
# emojis
s2 = re.sub(
    r':(\S+):',
    replace_emoji_name,
    s2
    )
"""