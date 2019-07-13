"""
from lxml import html, etree

xml = '<document><p>This is a test file! Hyperlink: <a href=\"https://www.google.de/\">https://www.google.de/</a></p></document>'

doc = etree.fromstring(xml)
etree.strip_tags(doc, "p")

print(etree.tostring(doc))
"""

import re
"""
text = '<document><p>This is a test file! Hyperlink: <a href=\"https://www.google.de/\">https://www.google.de/</a></p></document>'

# remove document tag
match = re.match(r'<document>(.+)<\/document>', text)
text = match.group(1)

# replace <p> with <br>
text = re.sub(r'<p>(.+)<\/p>', r'\1<br>', text)

print(text)
"""
text = 'Alliance Staging   Akidagi - Mans Got Home \r\n\r\nSWEG. TS :\r\n------------\r\nIP: ts.nohandlebars.space\r'
text = re.sub(r'\n|\r\n', r'<br>', text)
print(text)
