# @objection
👨‍⚖️ Hey, you can mention me in Slack threads to generate Ace Attorney scenes. I am currently installed on the [Hack Club Slack](https://slack.hackclub.com) but you still need to invite me to specific channels and mention my name in a thread to generate a scene.

## EXPERIMENTAL
Don't expect this bot to work perfectly at the moment. Currently, I am testing things before deploying this to a production environment.

Built upon [micah5](https://github.com/micah5) and [Eric Jiang](https://github.com/ericljiang)'s reddit bot: https://github.com/micah5/ace-attorney-reddit-bot so all credit goes to them.

#### Setup

- Create a new Slack App and add the following bot token scopes from "OAuth & Permissions": *app_mentions:read*, *channels:history*, *chat:write*, *users:read*
(__app_mentions__ is used to see when someone mentions our app in a channel, __channels:history__ is used to get the messages from a specific thread, __chat:write__ is used to send the generated gif link to the thread, and __users:read__ to get the display name of users who replied to the thread)
- Go to "Event Subscriptions", enable events and subscribe to the *app_mention* event
- Install the app to your Workspace from the "OAuth & Permissions" page, grab your "Bot User OAuth Access Token" and set it as the SLACK_BOT_TOKEN in your environment
- Under "Basic Information", grab the Signing Secret and set it as SLACK_SIGNING_SECRET in your environment
- Set the streamable_username and streamable_password variables in your environment if you want to upload to Streamable
- Install all the requirements and run "python bot_streamable.py"
- If you are developing locally, use ngrok to create a public url and put "{your_ngrok_url}/slack/events" to the "Request URL" under "Event Subscriptions"

#### Potential Issues / Ideas

- Currently, there is no parsing to see if a message contains markdown so generated gifs will look bad
- Should test how the animation scene behaves if a user's display name contains emojis
- We might use reactions added to a message to check the polarity of the message (i.e. sad, happy, neutral). Reddit version used the upvotes as a parameter
- There is currently a hard limit of 250 replies (bot doesn't generate a scene for threads containing more than 250 replies). Further testing is necessary to see if this is a good limit