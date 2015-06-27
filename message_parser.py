from flask import Flask, request, redirect
import twilio.twiml
import subprocess

#Parse the received text body (and the phone number) into something useful...
def parse_message_body(message_info):
    lower_case = message_info.body.lower()
    parsed_list = lower_case.split(' ')
    for i in range(len(parsed_list)):
        if parsed_list[i] == 'to' or parsed_list[i] == '-' or parsed_list[i] == 'x' or parsed_list[i] == 't' or parsed_list[i] == '2':
            from_station = ''
            to_station = ''
            for j in range(i):
                if j == (i - 1):
                    from_station += parsed_list[j]
                else:
                    from_station += parsed_list[j] + ' '
            for j in range((i + 1), len(parsed_list)):
                if j == (len(parsed_list) - 1):
                    to_station += parsed_list[j]
                else:
                    to_station += parsed_list[j] + ' '
            return subprocess.check_output(['python', 'mbta.py', '-s', to_station, from_station])
    if (len(parsed_list) >= 2):
        station = join_strings(parsed_list[0:-1])
        direction = parsed_list[-1]
        return subprocess.check_output(['python', 'mbta.py', '-d', direction, station])

def get_stations(message_info):
    lower_case = message_info.body.lower()
    parsed_list = lower_case.split(' ')
    for i in range(len(parsed_list)):
        if parsed_list[i] == 'to' or parsed_list[i] == '-' or parsed_list[i] == 'x' or parsed_list[i] == 't' or parsed_list[i] == '2':
            from_station = ''
            to_station = ''
            for j in range(i):
                if j == (i - 1):
                    from_station += parsed_list[j]
                else:
                    from_station += parsed_list[j] + ' '
            for j in range((i + 1), len(parsed_list)):
                if j == (len(parsed_list) - 1):
                    to_station += parsed_list[j]
                else:
                    to_station += parsed_list[j] + ' '
            return [from_station, to_station]
    if (len(parsed_list) == 1):
        return [parsed_list[0]]
    if (len(parsed_list) >= 2):
        station = join_strings(parsed_list[0:-1])
        direction = parsed_list[-1]
        return [station]

def favorite_keyword(keyword):
    keyword = keyword.lower().strip()
    return keyword == 'favorite' or keyword == 'fav' or keyword == 'fave'

def invalid_favorite(keyword):
    keyword = keyword.lower().strip()
    return keyword == 'favorite' or keyword == 'fav' or keyword == 'fave' or \
           keyword == 'cancel'

def join_strings(strings):
    output = ''
    for i in range(len(strings)):
        if i == (len(strings) - 1):
            output += strings[i]
        else:
            output += strings[i] + ' '
    return output
