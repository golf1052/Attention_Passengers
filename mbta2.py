import argparse
import requests
import json
import datetime
import time
import config

dev_api_key = 'wX9NwuHnZU2ToO7GmGR9uw'
real_api_key = config.real_api_key

time_format = ''

def get_directional_data(from_station, direction, time='12h'):
    global time_format
    if time == '24h':
        time_format = '%H:%M'
    else:
        time_format = '%I:%M %p'

    from_station = shorten_names(from_station)

def get_from_to_data(from_station, to_station):
    global time_format
    if time == '24h':
        time_format = '%H:%M'
    else:
        time_format = '%I:%M %p'

    from_station = shorten_names(from_station)
    to_station = shorten_names(to_station)
    from_station_id = _get_station_id(from_station)
    if from_station_id == None:
        return 'Could not find station ' + from_station
    to_station_id = _get_station_id(to_station)
    if to_station_id == None:
        return 'Could not find station ' + to_station
    # new stops file will contain
        # line station is on
        # station name (id)
        # inbound station stop id
        # outbound station stop id
    # 1 check to see if from and to stations are on the same line if so go to 2, if not go to 4
    # 2 get the next train times from the from station
    # 3 see what time that train will arrive at the to station
    # example instruction set
        # ruggles to downtown crossing
        # what time can we leave ruggles
        # what time will we get to downtown crossing

    # 4 THE HARD PART?! Find the transfer chain
        # the stops we must transfer at
        # example oak grove to riverside
            # transfer at north station to Green-E
            # transfer at park street to Green-D
        # example alewife to wonderland
            # transfer at downtown crossing to Orange
            # transfer at state to Blue
    # 5 get the next train times from the from station
    # 6 see what time that train will arrive at the transfer station
    # 7 transfer to the new line
    # 8 repeat 5 through 7 until we are on our to station line
    # example instruction set
        # also see above
        # alewife to wonderland is actually
        # alewife to downtown crossing
        # downtown crossing to state
        # state to wonderland


# Helper methods

def shorten_names(word):
    return word.replace('street', 'st').replace('str', 'st').replace('avenue', 'ave') \
               .replace('square', 'sq').replace('road', 'rd').replace('center', 'ctr') \
               .replace('circle', 'cir')

def _get_station_id(station):
    with open ('stops.json') as stops_file:
        stop_data = json.load(stops_file)

    if station not in stop_data:
        return None
        print "Station not found"
        raise ValueError("Station %s not found. You Suck." % station)
    else:
        return stop_data[station]