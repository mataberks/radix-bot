FROM python:3

ADD senjatrollet.py /

RUN pip install slackclient

RUN pip install paho-mqtt

EXPOSE 1883

CMD [ "python", "./senjatrollet.py" ]
