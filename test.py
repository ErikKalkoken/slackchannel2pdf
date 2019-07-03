import re

user_names = {
    "U123456789": "Naoko",
    "U623456789": "Janet",
    "U723456789": "Yuna"
}

channel_names = {
    "C123456789": "berlin",
    "C723456789": "tokio",
    "C423456789": "oslo"
}

s = "Hello <@U723456789> my friend, did you see the new channel <#C723456789>"
pattern = re.compile(r'<(.*?)>')

while True:
    m = pattern.search(s)    
    if m is not None:
        match = m.group(1)
        id_char = match[0]
        
        if id_char == "@":
            id = match[1:len(match)]
            if id in user_names:
                name = "@" + user_names[id]
            else:
                name = "(unknown user)"
        
        elif id_char == "#":
            id = match[1:len(match)]
            if id in channel_names:
                name = "#" + channel_names[id]
            else:
                name = "(unknown channel)"
        else:
            name = "(unknown)"
        
        start = m.span()[0]
        end = m.span()[1]
        s = s[0:start] + name + s[end:len(s)]
    else:
        break

print(s)



