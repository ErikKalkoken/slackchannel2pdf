import html


def transform_encoding(text):
    """adjust encoding to latin-1 and transform HTML entities"""
    text2 = html.unescape(text)
    text2 = text2.encode("utf-8", "replace").decode("utf-8")
    text2 = text2.replace("\t", "    ")
    return text2
