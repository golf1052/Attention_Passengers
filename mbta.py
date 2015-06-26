import argparse
import requests
import json
import datetime
import time
import config

dev_api_key = 'wX9NwuHnZU2ToO7GmGR9uw'
real_api_key = config.real_api_key
loaded_files = False
stops = None
stops_red_line_ashmont = None

stops_red_line_braintree = None
stops_orange_line = None

response_title = ""

def _load_json_files():
    global loaded_files
    global stops
    global stops_red_line_ashmont
    global stops_red_line_braintree
    global stops_orange_line
    if not loaded_files:
        with open('stops.json', 'r') as f:
            stops = json.load(f)
        with open('stops_red_line_ashmont.json', 'r') as f:
            stops_red_line_ashmont = json.load(f)
        with open('stops_red_line_braintree.json', 'r') as f:
            stops_red_line_braintree = json.load(f)
        with open('stops_orange_line.json', 'r') as f:
            stops_orange_line = json.load(f)
        loaded_files = True

def _parse_args():
    parser = argparse.ArgumentParser(description='Process MBTA requests')
    dest = parser.add_mutually_exclusive_group(required=True)

    parser.add_argument('start', help='Station to get data from')
    dest.add_argument('-d', '--direction', help='Direction (inbound or outbound)')
    dest.add_argument('-s', '--dest', help='Destination Station')

    return parser.parse_args()

###
# Helper methods
###
def send_request(endpoint, parameters):
    parameters['api_key'] = dev_api_key
    parameters['format'] = 'json'
    base_url = 'http://realtime.mbta.com/developer/api/v2/'
    r = requests.get(base_url + endpoint, params=parameters)

    #print r.url

    return r.json()

def _try_get_stop_id(station):
    _load_json_files()
    if station in stops:
        return stops[station]
    else:
        return None

####################
# MBTA API CALLS
####################
#Get schedule by station
def _get_departures_by_stop(train_id):
    payload = {'max_time': 600, 'stop': train_id}
    data = send_request('schedulebystop', payload)
    return data

###
# Alerts stuff
###
def _get_alerts_by_stop(stop):
    parameters = {'stop': stop}
    data = send_request('alertsbystop', parameters)
    return data

def _get_alerts_by_route(route):
    parameters = {'route': route}
    data = send_request('alertsbyroute', parameters)
    return data

def try_get_alerts(input):
    stop = _try_get_stop_id(input)
    return_messages = []
    if stop == None:
        return_messages.append('Station not found')
    else:
        alerts = _get_alerts_by_stop(stop)
        if len(alerts['alerts']) == 0:
            #return_messages.append('No alerts for this station')
            return return_messages
        else:
            active_alerts = []
            for alert in alerts['alerts']:
                # filter out bus alerts if alert only affects busses
                bus_alert = False
                for service in alert['affected_services']['services']:
                    if service['mode_name'] == 'Bus':
                        bus_alert = True
                    elif bus_alert:
                        bus_alert = False
                        break
                if bus_alert:
                    continue
                # filter out alerts that don't apply to today
                current_time = long(time.time())
                in_period = True
                for period in alert['effect_periods']:
                    if period['effect_end'] != '':
                        if current_time < long(period['effect_start']) or current_time > long(period['effect_end']):
                            in_period = False
                    else:
                        if current_time < period['effect_start']:
                            in_period = False
                if not in_period:
                    continue
                active_alerts.append(alert)
            if len(active_alerts) == 0:
                #return_messages.append('No alerts for this station')
                pass
            else:
                for alert in active_alerts:
                    alert_message = 'Alert! ' + alert['short_header_text']
                    return_messages.append(alert_message)
    return return_messages


####################
# JSON PARSING
####################

# Parse the next X departures for a specific train(inbound/outbound) at a station
def _next_departures(train_id, no_trains=3, start_time=0):
    global response_title
    schedule = _get_departures_by_stop(train_id)

    response_title = response_title + schedule['stop_name']

    departures = {}
    departure_ids = []

    for mode in schedule['mode']:
        if mode['mode_name'] == "Subway":

            for route in mode['route']:

                route_name = route['route_id']
                departures.setdefault(route_name, [])

                for direction in route['direction']:
                        for trip in direction['trip']:
                            while len(departures[route_name]) < no_trains:
                                if start_time > 0:
                                    if trip['sch_arr_dt'] < start_time:
                                        continue
                                    else:
                                        departures[route_name].append(int(trip['sch_arr_dt']))
                                        departure_ids.append(trip['trip_id'])
                                else:
                                    departures[route_name].append(int(trip['sch_arr_dt']))
                                    departure_ids.append(trip['trip_id'])


        break #don't look past subways
    deps_dict = {"departures": departures, "trip_ids": departure_ids}
    return deps_dict


# Get station_id from common station name (stops.json)
def _get_station_id(station):

    with open ('stops.json') as stops_file:
        stop_data = json.load(stops_file)

    if station not in stop_data:
        print "Station not found"
        raise ValueError("Station %s not found. You Suck." % station)
    else:
        return stop_data[station]


# Get json blob containing all train info for a station
# Example below
# {
#     "stations": [
#         {
#             "line": "red",
#             "stops": [
#                 {
#                     "stop_idx": "9",
#                     "inbound": "70077",
#                     "outbound": "70078",
#                     "stop_id": "place-dwnxg"
#                 }
#             ]
#         },
#         {
#             "line": "orange",
#             "stops": [
#                 {
#                     "stop_idx": "10",
#                     "inbound": "70020",
#                     "outbound": "70021",
#                     "stop_id": "place-dwnxg"
#                 }
#             ]
#         }
#     ]
# }

def _get_station_blob(station_id):
    with open ('lines.json') as stop_file:
        stop_data = json.load(stop_file)


    station_blob = {'stations': []}
    #Return json blob
    for line in stop_data['lines']:
        for stop in line['stops']:
            if stop['stop_id'] == station_id:
                line_blob = {"line": line['name'], "stops": [stop]}
                #line['stops'].append(stop)
                station_blob['stations'].append(line_blob)

    return station_blob


####################
# MAIN STUFF
####################

#Get the next X departures given the direction of travel (inbound/outbound)
def _get_departures_by_dir(from_station, direction):

    response = ""
    global response_title
    response_list = []
    station_id = _get_station_id(from_station)
    station_blob = _get_station_blob(station_id)

    #print json.dumps(station_blob, indent=4)

    for station in station_blob['stations']:
        for stop in station['stops']:
            train_id = stop[direction]
            departures = _next_departures(train_id)['departures']

            if len(departures) > 1 :
                for key in departures:
                    title = response_title + " (" + _get_title(key) + ")"
                    response = response + "\n" + title
                    for time in departures[key]:
                        time_str = datetime.datetime.fromtimestamp(time).strftime('%H:%M')
                        response = response + "\n" + time_str
            else:
                for key in departures:
                    response = response + response_title
                    for time in departures[key]:
                        time_str = datetime.datetime.fromtimestamp(time).strftime('%H:%M')
                        response = response + "\n" + time_str

    response_list.append(response)
    print response
    return response_list

def _get_title(route_id):
    if route_id == '931_':
        return "Ashmont"
    elif route_id == '933_':
        return "Braintree"


def _get_same_line(x, y):

    x_lines = _get_lines(x)
    y_lines = _get_lines(y)

    line_set = (set(x_lines) & set(y_lines))
    if line_set:
        return line_set.pop()
    else:
        return False

def _get_station_index(station_blob, line):
    for station in station_blob['stations']:
            if station['line'] == line:
                for stop in station['stops']:
                    return int(stop['stop_idx'])

def _get_pivot_index(line_name):
    with open ('lines.json') as stop_file:
        stop_data = json.load(stop_file)

    for line in stop_data['lines']:
        if line['name'] == line_name:
            return int(line['pivot_idx'])


#Get lines available at a station
def _get_lines(station_blob):
    lines = []

    for station in station_blob['stations']:
        lines.append(station['line'])

    return lines

#Get intermediate station to transfer from Station A to Station B (using the blobs of course)
def _get_transfer(from_st, to_st):

    from_lines = _get_lines(from_st)
    to_lines = _get_lines(to_st)
    transfer_station = ""
    transfer_line = ""

    for aline in from_lines:
        for bline in to_lines:
            result = _can_transfer(aline, bline)
            if result:
                transfer_station = result
                transfer_line = aline

    transfer = {"station": transfer_station, "line": transfer_line}
    return transfer

# Helper for _get_transfer(). Checks for a specific line rather than a list
def _can_transfer(from_line, to_line):

    with open('lines.json') as stop_file:
        stop_data = json.load(stop_file)

    for line in stop_data['lines']:
        if line['name'] == from_line:
            for transfer in line['transfers']:
                if to_line in transfer:
                    return transfer[to_line]

def _get_direction(start_idx, dest_idx, pivot):
    direction = ""

    if start_idx <= pivot:
        if start_idx < dest_idx:
            direction = "inbound"
        elif start_idx > dest_idx:
            direction = "outbound"

    elif start_idx > pivot:
        if start_idx < dest_idx:
            direction = "outbound"
        elif start_idx > dest_idx:
            direction = "inbound"

    return direction

#Returns an key/value dict of the next 3 departures
def _get_departures_by_dest_helper(start_blob, dest_blob, line, no_departures=3, start_time=0):

    #Get indices
    start_idx = _get_station_index(start_blob, line)
    dest_idx = _get_station_index(dest_blob, line)
    pivot = _get_pivot_index(line)

    direction = _get_direction(start_idx, dest_idx, pivot)

    for station in start_blob['stations']:
        if station['line'] == line:
            for stop in station['stops']:
                train_id = stop[direction]
                return _next_departures(train_id, no_departures, start_time)


#Get the next X departures given the destination
def _get_departures_by_dest(from_station, dest):
    response = ""
    global response_title
    response_list = []

    start_station = _get_station_id(from_station)
    dest_station = _get_station_id(dest)

    # Get station json blobs for start/end
    start_blob = _get_station_blob(start_station)
    #print json.dumps(start_blob, indent=4)
    dest_blob = _get_station_blob(dest_station)
    #print json.dumps(dest_blob, indent=4)

    #Check if we need to transfer
    line = _get_same_line(start_blob, dest_blob)

    # We're on different lines...shit
    if not line:
        transfer = _get_transfer(start_blob, dest_blob)
        #print json.dumps(transfer, indent=4)
        trans_blob = _get_station_blob(transfer['station'])
        #print json.dumps(trans_blob, indent=4)

        departures = _get_departures_by_dest_helper(start_blob, trans_blob, transfer['line'])
        print departures
        header = from_station + " " + dest + "Transfer"

        for key in departures['departures']:
            for idx, time in enumerate(departures['departures'][key]):
                print idx
                time_str = datetime.datetime.fromtimestamp(time).strftime('%H:%M')
                response = response + "\n" + _transfer(time_str, departures['trip_ids'][idx], trans_blob, dest_blob)

    else:
        departures = _get_departures_by_dest_helper(start_blob, dest_blob, line)['departures']

        if len(departures) > 1 :
            for key in departures:
                title = response_title + " (" + _get_title(key) + ")"
                response = response + "\n" + title
                for time in departures[key]:
                    time_str = datetime.datetime.fromtimestamp(time).strftime('%H:%M')
                    response = response + "\n" + time_str
        else:
            for key in departures:
                response = response + response_title
                for time in departures[key]:
                    time_str = datetime.datetime.fromtimestamp(time).strftime('%H:%M')
                    response = response + "\n" + time_str

    ##print response
    response_list.append(response)
    print response
    return response_list

# Deal with transfers. It's 11am after hackbeanpot..i don't feel like writing documentation
def _transfer(response, trip_id, trans_station_blob, dest_blob):

    line = _get_same_line(trans_station_blob, dest_blob)
    trans_arrival = _get_arrival_time(trip_id, trans_station_blob, line)

    #trans_arrival = 1424016720
    line = _get_same_line(trans_station_blob, dest_blob)

    departures = _get_departures_by_dest_helper(trans_station_blob, dest_blob, line, 1, trans_arrival)['departures']

    for key in departures:
        for time in departures[key]:
            time_str = datetime.datetime.fromtimestamp(time).strftime('%H:%M')
            response = response + " | " + time_str

    return response

#Get arrival time of a
def _get_arrival_time(trip_id, station_blob, line):

    index = _get_station_index(station_blob, line)
    trip = send_request('schedulebytrip', {'trip':trip_id})

    for stop in trip['stop']:
        if stop['stop_sequence'] == index:
            return stop['sch_arr_dt']


def main():
    args = _parse_args()

    from_station = args.start
    #station_blob = _get_station_blob(_get_station_id('dtx'))
    #print json.dumps(station_blob, indent=4)

    if args.direction:
        departures = _get_departures_by_dir(from_station, args.direction)

    else:
        departures = _get_departures_by_dest(from_station, args.dest)

if __name__ == '__main__':
    main()
