import re

s = "this is some *bold* text"

s2 = re.sub(
    r'[*]([^*]+)[*]',
    r'<b>\1</b>',
    s
)

print(s2)

