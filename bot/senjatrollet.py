# coding: utf-8

import os
import time
from datetime import datetime
import threading
from slackclient import SlackClient


# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")
print('bot_id is ' + BOT_ID)

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"
STATUS_COMMAND = "temp"
COUNTING_COMMAND = "sau"

#TODO: encapsulate in some observable world 
sheepCounter = 0

#TODO: Read last stored state
degrees = 0.0
lastSensorTime = datetime.now()

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

import paho.mqtt.client as mqtt

# Initiate MQTT Client
mqttc = mqtt.Client()

MQTT_USERNAME = os.environ.get('MQTT_USERNAME')
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD')

# Define Variables
MQTT_HOST = "broker.shiftr.io"
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC = "sb/e1/kjk/t"
#MQTT_TOPIC = "tst/#"
MQTT_MSG = "hello MQTT"

#Mute temperature alarm
alarm_temp_low_mute = False

# Define on connect event function
# We shall subscribe to our Topic in this function
def on_connect(mosq, obj, rc):
    mqttc.subscribe(MQTT_TOPIC, 1)

# Define on_message event function. 
# This function will be invoked every time,
# a new message arrives for the subscribed topic 
def on_message(mosq, obj, msg):
    global degrees
    global lastSensorTime
    global alarm_temp_low_mute
    print("Topic: " + str(msg.topic))
    print("QoS: " + str(msg.qos))
    print("Payload: " + str(msg.payload))
    degrees = float(msg.payload)
    lastSensorTime = datetime.now()

    # TODO: Store message

    # Check range of reading
    if (degrees > 30.0):
        alarmMessage("Veldig høy temperatur, " + str(degrees) + "°C")
    elif (degrees < 5.0):
        if not alarm_temp_low_mute:
            alarmMessage("Veldig lav temperatur, " + str(degrees) + "°C")
            alarm_temp_low_mute = True
            alarmMessage("Holder tilbake alarm")
    elif alarm_temp_low_mute:
            alarmMessage("Temperatur tilbake til normalt område, " + str(degrees) + "°C")
            alarm_temp_low_mute = False


def on_subscribe(mosq, obj, mid, granted_qos):
    print("Subscribed to Topic: " + 
    MQTT_TOPIC + " with QoS: " + str(granted_qos))


def mqttSubThread():

    # Assign event callbacks
    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe

    # Connect with MQTT Broker
    mqttc.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
    mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)

    # Continue monitoring the incoming messages for subscribed topic
    mqttc.loop_forever()


def alarmMessage(message):
    print('Sender til slack: ' + message)
    slack_client.api_call("chat.postMessage", channel="alarm",
                  text=message, as_user=True)

def watchdogThread():
    global sheepCounter
    global lastSensorTime
    while(True):
        # Simulate some process
        sheepCounter += 1
        print("Sheep count is now " + str(sheepCounter))

        # Check if sensors are alive
        if ((datetime.now() - lastSensorTime).total_seconds() > 3600):
            alarmMessage("Ingen sensordata den siste timen!")
            lastSensorTime = datetime.now()

        time.sleep(600)


def handle_command(command, channel):
    response = "Ikke sikker på hva du mener. Bruk kommandoen *" + EXAMPLE_COMMAND + \
               "* ."
    if command.startswith(EXAMPLE_COMMAND):
        response = "Javel... kan jeg det?"

    if command.startswith(STATUS_COMMAND):
    	response = "Temperaturen på kjøkkenet er nå " + str(degrees) + "°C"

    if command.startswith(COUNTING_COMMAND):
        response = "Har til nå sett " + str(sheepCounter) + " sauer."

    slack_client.api_call("chat.postMessage", channel=channel,
                          text='radix '+response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


def chatThread():
    global sheepCounter
    global degrees
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")


if __name__ == "__main__":
    # Establish 3 threads: 
    #  - One watchdog, simulating sheep counting and some alarms
    #  - one subscribing to messages from sensors 
    #  - and one to serve slack chat
    #TODO:  Split in watchdog and simulating threads using different resolution
    threadWatchdog = threading.Thread(target=watchdogThread, args=[])
    threadWatchdog.start()
    threadMqtt = threading.Thread(target=mqttSubThread, args=[])
    threadMqtt.start()
    threadChat = threading.Thread(target=chatThread, args=[])
    threadChat.start()
