# Slack related logic

import json
from time import sleep

# limits for fetching messages from Slack
MESSAGES_PER_PAGE = 200
MAX_MESSAGES = 1000
MAX_MESSAGES_PER_THREAD = 500


def fetch_messages_for_channel(client, channel_id, max_messages = MAX_MESSAGES):
    """ retrieve messages from a channel on Slack """    
    messages_per_page = min(MESSAGES_PER_PAGE, max_messages)
    # get first page
    page = 1
    print("Retrieving page {}".format(page))
    response = client.conversations_history(
        channel=channel_id,
        limit=messages_per_page,
    )
    assert response["ok"]
    messages_all = response['messages']

    # get additional pages if below max message and if they are any
    while len(messages_all) + messages_per_page <= max_messages and response['has_more']:
        page += 1
        print("Retrieving page {}".format(page))
        sleep(1)   # need to wait 1 sec before next call due to rate limits
        response = client.conversations_history(
            channel=channel_id,
            limit=messages_per_page,
            cursor=response['response_metadata']['next_cursor']
        )
        assert response["ok"]
        messages = response['messages']
        messages_all = messages_all + messages

    print(
        "Fetched a total of {} messages from channel {}".format(
            len(messages_all),
            channel_id
    ))

    return messages_all

def read_messages_from_file(filename):
    """ reads list of message from a json file and returns it """     
    filename += '.json'
    with open(filename, 'r') as f:
        messages = json.load(f)
    print("read {} message from file: name {}".format(
        len(messages),
        filename
    ))
    return messages


def write_messages_to_file(messages, filename = 'messages'):
    """ writes list of message to a json file """     
    filename += '.json' 
    with open(filename , 'w', encoding='utf-8') as f:
        json.dump(
            messages, 
            f, 
            sort_keys=True, 
            indent=4, 
            ensure_ascii=False
            )
    print("written message to file: name {}".format(filename))
   

def fetch_messages_for_thread(client, channel_id, thread_ts, max_messages = MAX_MESSAGES_PER_THREAD):
    """ retrieve messages from a thread on Slack """    
    messages_per_page = min(MESSAGES_PER_PAGE, max_messages)
    # get first page
    page = 1
    print("Retrieving page {}".format(page))
    response = client.conversations_replies(
        channel=channel_id,
        ts=thread_ts,
        limit=messages_per_page
    )
    assert response["ok"]
    messages_all = response['messages']

    # get additional pages if below max message and if they are any
    while len(messages_all) + messages_per_page <= max_messages and response['has_more']:
        page += 1
        print("Retrieving page {}".format(page))
        sleep(1)   # need to wait 1 sec before next call due to rate limits
        response = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            limit=messages_per_page,
            cursor=response['response_metadata']['next_cursor']
        )
        assert response["ok"]
        messages = response['messages']
        messages_all = messages_all + messages

    print(
        "Fetched a total of {} messages from thread in channel {} with ts {}".format(
            len(messages_all),
            channel_id,
            thread_ts
    ))

    return messages_all


def fetch_threads_for_messages(client, channel_id, messages, max_messages = MAX_MESSAGES_PER_THREAD):
    """ returns all threads for provided of a channel """    
    threads = dict()
    for msg in messages:
        if "thread_ts" in msg and msg["thread_ts"] == msg["ts"]:
            thread_ts = msg["thread_ts"]
            thread_messages = fetch_messages_for_thread(
                client, 
                channel_id, 
                thread_ts,
                max_messages
            )            
            threads[thread_ts] = thread_messages
    return threads


def add_key(arr, col_name):
    """ adds key to a list and returns it as dict """
    arr2 = dict()
    for item in arr:
        key = item[col_name]
        arr2[key] = item
    return arr2


def reduce_to_dict(arr, key_name, col_name_primary, col_name_secondary=None):
    """ 
    reduces a list of dicts to one dict by selecting a key and a value column
    column with key_name will become the key
    colum with col_name_primary will become the value if it exists
    otherwise col_name_secondary will become he value if it exists and given
    otherwise the item will be ignored

    """
    arr2 = dict()
    for item in arr:
        if key_name in item:
            key = item[key_name]
            if col_name_primary in item:
                arr2[key] = item[col_name_primary]
            elif col_name_secondary is not None and col_name_secondary in item:
                arr2[key] = item[col_name_secondary]            
    return arr2


def fetch_user_names(client):    
    """ returns dict of user names with user ID as key """
    response = client.users_list()
    assert response["ok"]    
    user_names = reduce_to_dict(response["members"], "id", "real_name", "name")
    return user_names    


def fetch_channel_names(client):
    """ returns dict of channel names with channel ID as key """
    response = client.conversations_list(types="public_channel,private_channel")
    assert response["ok"]    
    channel_names = reduce_to_dict(response["channels"], "id", "name")
    return channel_names    
    