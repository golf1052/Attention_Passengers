from flask import Flask, request, redirect, render_template
import message_parser
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from parse_rest.connection import register
import passengers
from passenger import Message, Passenger, Favorite
import mbta
import mbta2
import subprocess
from parse_rest.query import QueryResourceDoesNotExist
import config
import subprocess

app = Flask(__name__)

account_sid = config.account_sid
auth_token = config.auth_token
twilio_number = config.twilio_number

@app.route('/', methods=['GET', 'POST'])
def respond():
    # load api's
    client = Client(account_sid, auth_token)
    response = MessagingResponse()

    # load message
    message_info = load_message(request)

    #there is no message, return the website instead
    if message_info.body == None:
        return render_template('index.html')

    # parse message to get body
    parsed_body = message_parser.parse_message_body(message_info)

    mbta_result = run_request(parsed_body, '12h')

    # read message and figure out what they need
    alerts_output = []

    # send responses
    final_output = []
    stations_list = message_parser.get_stations(message_info)
    for station in stations_list:
        station = mbta.shorten_names(station)
        alerts_output.extend(mbta.try_get_alerts(station))
    alerts_set = set(alerts_output)
    alerts_output = list(alerts_set)
    append_messages(final_output, mbta_result)
    final_output.extend(alerts_output)
    if len(final_output) > 1:
        for m in final_output[0:-1]:
            send_message(client, message_info.number, m)
    message = final_output[-1]
    response.message(message)
    return str(response)

def append_messages(output, messages):
    for message in messages:
        output.append(message)
    return output

def load_message(request):
    message_info = passengers.MessageInfo(
        request.values.get('MessageSid'), request.values.get('From'),
        request.values.get('Body'), request.values.get('NumMedia'),
        request.values.get('FromCity'), request.values.get('FromState'),
        request.values.get('FromZip'), request.values.get('FromCountry'),
        request.values.get('SmsStatus'))
    return message_info

def load_last_message(client, sid):
    message = client.messages.get(sid)
    return passengers.load_message_info(message)

def send_message(client, to, body):
    client.messages.create(to=to, from_=twilio_number, body=body)

def run_request(parsed_body, time_format='12h'):
    if parsed_body.return_type == 'dir':
        pass
    elif parsed_body.return_type == 'dest':
        m = mbta2.MbtaO()
        return m.get_from_to_data(parsed_body.result[0], parsed_body.result[1], time_format)
    elif parsed_body.return_type == 'other':
        return parsed_body.result[0]
    else:
        return None

if __name__ == '__main__':
    app.run(port=5432, debug=False)
