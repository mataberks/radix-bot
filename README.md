

## Setup
Based on https://www.fullstackpython.com/blog/build-first-slack-bot-python.html

```
git clone this repo

virtualenv -p python3 senjabot

source senjabot/bin/activate

cd senjabot

pip install slackclient

pip install paho-mqtt


export SLACK_BOT_TOKEN='---'
export BOT_ID='---'
export MQTT_USERNAME='---'
export MQTT_PASSWORD='---'

python senjatrollet.py

```

## Service
Make sure it allways run do:
```sudo systemctl start senjabot```
In crontab add:
05 0 * * * sudo systemctl reload-or-restart senjabot


## Send test messages
Use tool_pub


