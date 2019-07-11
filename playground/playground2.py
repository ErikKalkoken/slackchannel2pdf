import channelexport
import json

try:
    with open("fonts/emoji.json", 'r', encoding="utf-8") as f:
        emojis = json.load(f)
    map = channelexport.reduce_to_dict(emojis, "short_name", "unified")
except Exception as e:
    print("WARN: failed to load emojis", e)
    map = []


try:
    with open("emoji_map.json" , 'w', encoding="utf-8") as f:
        json.dump(
            map, 
            f, 
            sort_keys=True, 
            indent=4, 
            ensure_ascii=False
            )
except Exception as e:
    print("ERROR: failed to write to {}: ".format(filename), e)        

