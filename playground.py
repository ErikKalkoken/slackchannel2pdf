
my_list = [
    {"id": "one", "name": "Naoko", "ts": 89.4},
    {"id": "two", "name": "Janet", "ts": 100.2},
    {"id": "three", "name": "Rosie", "ts": 76.2},
    {"id": "four", "name": "Erik", "ts": 96.1}
]

my_list = sorted(my_list, key=lambda k: k['ts'])

print(my_list)


