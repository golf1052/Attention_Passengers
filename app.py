from flask import Flask, request, redirect, render_template
import message_parser
import twilio.twiml
from twilio.rest import TwilioRestClient
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
parse_app = config.parse_app
parse_rest = config.parse_rest

@app.route('/', methods=['GET', 'POST'])
def respond():
    # load api's
    client = TwilioRestClient(account_sid, auth_token)
    register(parse_app, parse_rest)
    response = twilio.twiml.Response()

    # load message
    message_info = load_message(request)

    #there is no message, return the website instead
    if message_info.body == None:
        return render_template('index.html')

    # get user from parse
    user = passengers.check_for_user(message_info)

    if message_info.body == '12':
        user.timeFormat = '12h'
        user.save()
        response.message("Time format changed to 12 hour")
        return str(response)
    elif message_info.body == '24':
        user.timeFormat = '24h'
        user.save()
        response.message("Time format changed to 24 hour")
        return str(response)

    if user.fState == "Keyword":
        # currently setting up keyword
        tmpKeyword = message_info.body
        tmpKeyword = tmpKeyword.lower()
        if message_parser.invalid_favorite(tmpKeyword):
            # user is a butt, used an invalid word
            response.message("You can't set " + message_info.body + " as a favorite...")
            return str(response)
        elif tmpKeyword == "bla":
            # canceled favorite creation
            user.fState = "None"
            user.save()
            response.message("Favorite creation canceled")
            return str(response)
        else:
            # got a keyword, save it in the user object (easiest way?)
            user.fKeyword = message_info.body
            user.fState = "Query"
            user.save()
            response.message("Ok, what's the query?")
            return str(response)
    elif user.fState == "Query":
        # currently setting up query
        tmpQuery = message_info.body
        tmpQuery = tmpQuery.lower()
        if message_parser.invalid_favorite(tmpQuery):
            # user again is a butt
            response.message("You can't set " + message_info.body + " as a query...")
            return str(response)
        elif tmpQuery == "bla":
            # canceled favorite creation
            user.fState = "None"
            user.save()
            response.message("Favorite creation canceled")
            return str(response)
        else:
            # got a query
            favorite = Favorite(keyword=user.fKeyword, query=message_info.body)
            favorite.save()
            user.favorites.append(favorite)
            user.fKeyword = ""
            user.fState = "None"
            user.save()
            response.message("Favorite saved! Keyword: " + favorite.keyword + " Query: " + favorite.query)
            return str(response)
    elif user.fState == "None":
        # default to none
        if message_parser.favorite_keyword(message_info.body):
            user.fState = "Keyword"
            user.save()
            response.message("So I see you want to make a favorite, what's the keyword?")
            return str(response)
        else:
            # do literally anything else
            pass

    # parse message to get body
    parsed_body = message_parser.parse_message_body(message_info)

    if parsed_body.return_type == 'other':
        if len(user.favorites) > 0:
            try:
                favorite_kw = Favorite.Query.get(keyword=parsed_body.result[0])
                if favorite_kw.objectId in user.favorites:
                    query = passengers.MessageInfo(None, None, favorite_kw.query, None, None, None, None, None, None)
                    parsed_body = message_parser.parse_message_body(query)
            except QueryResourceDoesNotExist:
                pass

    mbta_result = run_request(parsed_body, user.timeFormat)

    # read message and figure out what they need
    alerts_output = []

    # check mbta for info

    # save last message data to parse
    save_last_message(user, message_info)

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

def save_last_message(user, message_info):
    recent_message = Message(sid=message_info.sid)
    recent_message.save()
    user.messages.append(recent_message)
    user.save()

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
