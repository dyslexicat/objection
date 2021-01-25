import os
import re
from pathlib import Path
from dotenv import load_dotenv
from tinydb import TinyDB, Query
from typing import List, Dict
import anim
from collections import Counter
import spaw
import re
import time

import logging
logging.basicConfig(level=logging.ERROR)

from slack_bolt import App

env_path = Path(".") / '.env'
load_dotenv(dotenv_path=env_path)
MESSAGES_PER_PAGE = 100

streamable_username = os.environ.get("streamable_username")
streamable_password = os.environ.get("streamable_password")

app = App()

_spaw = spaw.SPAW()
_spaw.auth(streamable_username, streamable_password)

db = TinyDB("db.json")

BOT_ID = app.client.api_call("auth.test")["user_id"]

# ThreadComment class to represent important fields of thread replies
class ThreadReply:
    def __init__(self, text, author, ts):
        self.text = text
        self.author = author
        self.ts = ts

    def __repr__(self):
        return f"Thread reply by {self.author}. ts: {self.ts} // text: {self.text}"

# get a list of replies from the thread data
def get_replies(messages: List, usernames: List) -> List:
    return [ThreadReply(text=strip_message_text(message["text"], usernames), author=message["user"], ts=message["ts"]) for message in messages]

# create a map from ids to display names (might include emojis?)
def get_usernames(ids: List[str]) -> Dict[str, str]:
    username_map = {}
    for id in ids:
        display_name = get_displayname(id)
        username_map[id] = display_name

    return username_map

# get the display name of a user from the id
# TEST: what happens if a user has an emoji in their display name
def get_displayname(id: str) -> str:
    response = app.client.users_info(user=id)
    if response["ok"]:
        return response["user"]["profile"]["display_name"]
    else:
        raise Exception

# get a markdown removed version of the message / with usernames replaced
def strip_message_text(message: str, usernames: List[str]) -> str:
    ids = re.findall(r"<(.*?)>", message)

    for id in ids:
        if not id.startswith("@U"):
            continue
        
        # remove the @ from the id before checking
        id = id[1:]

        if id == BOT_ID:
            display_name = "objection-bot"
        elif id in usernames:
            display_name = usernames[id]
        else:
            display_name = get_displayname(id)

        message = message.replace(f"<@{id}>", f"@{display_name}")

    return message

#debugging cursor pagination
def get_msg_ids(messages: List) -> set:
    return set([msg.get("client_msg_id", "") for msg in messages])

# slack app mention event
@app.event('app_mention')
def handle_mention(event, client, ack):
    print(event)
    ack()
    channel_id = event.get("channel")
    user_id = event.get("user")
    Thread = Query()

    thread_ts = event.get('thread_ts')

    #check that we are in fact in a thread
    if thread_ts:
        thread_data = client.conversations_replies(channel=channel_id, ts=thread_ts, limit=MESSAGES_PER_PAGE)
        assert thread_data["ok"]
        messages_all = thread_data["messages"]

        #pagination
        while thread_data["has_more"]:
            time.sleep(1)
            thread_data = client.conversations_replies(channel=channel_id, ts=thread_ts, limit=MESSAGES_PER_PAGE, cursor=thread_data["response_metadata"]["next_cursor"])
            assert thread_data["ok"]
            messages = thread_data["messages"]
            messages_all += messages

        #reply_count = messages_all[0]["reply_count"]
        #reply_users_count = messages_all[0]["reply_users_count"]
        reply_users = messages_all[0]["reply_users"]
    
        usernames = get_usernames(reply_users)
        replies = get_replies(messages_all, usernames)

        if len(db.search(Thread.ts == thread_ts)) == 0:
            try:
                # adding to database
                db.insert({"ts": thread_ts})

                if len(messages_all) > 250:
                    client.post_chatMessage(channel=channel_id, ts=thread_ts, limit=MESSAGES_PER_PAGE, text="too many messages in this thread :(")
                    return

                print(f"generating video for {thread_ts}")
                # handle metadata
                print(f"handling metadata...")

                authors = [reply.author for reply in replies]
                most_common = [t[0] for t in Counter(authors).most_common()]

                #generate video
                output_filename = f"{user_id}-{thread_ts}.mp4"
                print(f"generating video {output_filename}...")
                characters = anim.get_characters(most_common)

                #replies[:-1] because last reply is the bot command
                anim.comments_to_scene(usernames, replies[:-1], characters, output_filename=output_filename)

                #upload video
                print(f"uploading video...")
                response = _spaw.videoUpload(output_filename)

                RESPONSE_MSG = [{'type': 'section', 'text': {'type':'mrkdwn', 'text': ("Here's your video :judge:\n" f"https://streamable.com/{response['shortcode']}")}}]
                msg_response = client.chat_postMessage(channel=channel_id, thread_ts=thread_ts, blocks=RESPONSE_MSG)

                if not msg_response["ok"]:
                    print(f"There was an error sending the message for streamable shortcode: {response['shortcode']}")
                
                # if everything was ok let's remove the output file
                if msg_response["ok"] and response["status"]:
                    os.remove(f"{thread_ts}.mp4")

                print(f"done generating video for {thread_ts}")
            except Exception as e:
                print(e)


if __name__ == "__main__":
    app.start(5000)