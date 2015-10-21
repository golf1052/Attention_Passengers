import argparse
import requests
import json
import datetime
import time
import config
import copy

dev_api_key = 'wX9NwuHnZU2ToO7GmGR9uw'
real_api_key = config.real_api_key

class MbtaO:
    def __init__(self):
        self.time_format = ''

        # json files
        self.file_transfers = None

        self.stops_by_route_cache = []
        self.routes_by_stop_cache = []
        self.lowest_chain = None

    def get_from_to_data(self, from_station, to_station, time='12h'):
        if time == '24h':
            self.time_format = '%H:%M'
        else:
            self.time_format = '%I:%M %p'

        from_station = shorten_names(from_station)
        to_station = shorten_names(to_station)
        from_station_id = _get_station_id(from_station)
        if from_station_id == None:
            return 'Could not find station ' + from_station
        to_station_id = _get_station_id(to_station)
        if to_station_id == None:
            return 'Could not find station ' + to_station
        self.file_transfers = _load_json_file('transfers.json')
        from_station_route_data = self._retrieve_routes_by_stop_cached(from_station_id)
        to_station_route_data = self._retrieve_routes_by_stop_cached(to_station_id)
        from_station_lines = _lines_from_routes_data(from_station_route_data)
        to_station_lines = _lines_from_routes_data(to_station_route_data)
        self._try_find_transfer_chain(from_station_id, to_station_id, from_station_lines, to_station_lines, TransferChain(), self.file_transfers)
        if self.lowest_chain == None:
            return 'Could not find route from ' + from_station + ' to ' + to_station
        messages = [TransferMessage(), TransferMessage(), TransferMessage()]
        for i in range(len(messages)):
            for transfer in self.lowest_chain.transfers:
                num_trips = 1
                if messages[i].time == None:
                    num_trips = 3
                departures = _retrieve_schedule_by_stop(transfer._from_id, num_trips, messages[i].time)
                for mode in departures['mode']:
                    for route in mode['route']:
                        for direction in route['direction']:
                            arrivals = None
                            count = 0
                            if len(direction['trip']) == 3:
                                count = i
                            else:
                                count = 0
                            arrivals = _retrieve_schedule_by_trip(direction['trip'][count]['trip_id'])
                            for stop in arrivals['stop']:
                                if stop['stop_id'] == transfer.to_id:
                                    messages[i].message += transfer._from_name + ' to ' + transfer.to_name + '\n'
                                    f_time = datetime.datetime.fromtimestamp(int(direction['trip'][count]['sch_dep_dt'])).strftime(self.time_format)
                                    t_time = datetime.datetime.fromtimestamp(int(stop['sch_arr_dt'])).strftime(self.time_format)
                                    messages[i].message += f_time + ' - ' + t_time + '\n'
                                    messages[i].total_time += int(stop['sch_arr_dt']) - int(direction['trip'][count]['sch_dep_dt'])
                                    messages[i].time = int(stop['sch_arr_dt'])
                                    break
            messages[i].message += 'Total: ' + str(datetime.timedelta(seconds=messages[i].total_time))
        return_messages = []
        for message in messages:
            return_messages.append(message.message)
        return return_messages

    def _try_find_transfer_chain(self, from_station, to_station, from_station_lines, to_station_lines, transfer_chain, file_transfers):
        for to_line in to_station_lines:
            for from_line in from_station_lines:
                if from_line['route_id'] == to_line['route_id']:
                    _from_line_stops = self._retrieve_stops_by_route_cached(from_line['route_id'])
                    for direction in _from_line_stops['direction']:
                        _station_index = 0
                        for i in range(len(direction['stop'])):
                            if direction['stop'][i]['parent_station'] == from_station:
                                _station_index = i
                                break
                        for i in range(_station_index + 1, len(direction['stop']), 1):
                            if direction['stop'][i]['parent_station'] == to_station:
                                done_transfer_chain = copy.deepcopy(transfer_chain)
                                done_transfer_chain.add_transfer(from_station, direction['stop'][_station_index]['stop_id'], direction['stop'][_station_index]['parent_station_name'], to_station, direction['stop'][i]['stop_id'], direction['stop'][i]['parent_station_name'], from_line['route_id'])
                                if self.lowest_chain == None:
                                    self.lowest_chain = done_transfer_chain
                                else:
                                    if len(done_transfer_chain.transfers) < len(self.lowest_chain.transfers):
                                        self.lowest_chain = done_transfer_chain
                                return done_transfer_chain
                    return None
                from_line_stops = self._retrieve_stops_by_route_cached(from_line['route_id'])
                for direction in from_line_stops['direction']:
                    station_index = 0
                    for i in range(len(direction['stop'])):
                        if direction['stop'][i]['parent_station'] == from_station:
                            station_index = i
                            break
                    # now look for transfer stations
                    current_transfers = _get_transfer_list(from_line['route_id'], file_transfers)
                    for i in range(station_index + 1, len(direction['stop']), 1):
                        for transfer in current_transfers:
                            if direction['stop'][i]['parent_station'] == transfer['station']:
                                if not transfer_chain.contains_already(transfer['station'], from_line['route_id']):
                                    new_transfer_chain = copy.deepcopy(transfer_chain)
                                    new_transfer_chain.tries += 1
                                    if new_transfer_chain.tries > 4:
                                        # we've gone too far
                                        return None
                                    new_transfer_chain.add_transfer(from_station, direction['stop'][station_index]['stop_id'], direction['stop'][station_index]['parent_station_name'], transfer['station'], direction['stop'][i]['stop_id'], direction['stop'][i]['parent_station_name'], from_line['route_id'])
                                    new_from_station = transfer['station']
                                    new_from_station_route_data = self._retrieve_routes_by_stop_cached(new_from_station)
                                    new_from_station_lines = _lines_from_routes_data(new_from_station_route_data)
                                    self._try_find_transfer_chain(new_from_station, to_station, new_from_station_lines, to_station_lines, new_transfer_chain, file_transfers)
        return None
        # ¯\_(ツ)_/¯

    def _retrieve_routes_by_stop_cached(self, stop):
        for routes in self.routes_by_stop_cache:
            if routes[0] == stop:
                return routes[1]
        new_route = _retrieve_routes_by_stop(stop)
        self.routes_by_stop_cache.append((stop, new_route))
        return new_route

    def _retrieve_stops_by_route_cached(self, stop):
        for stops in self.stops_by_route_cache:
            if stops[0] == stop:
                return stops[1]
        new_stop = _retrieve_stops_by_route(stop)
        self.stops_by_route_cache.append((stop, new_stop))
        return new_stop

# Helper methods

def shorten_names(word):
    return word.replace('street', 'st').replace('str', 'st').replace('avenue', 'ave') \
               .replace('square', 'sq').replace('center', 'ctr') \
               .replace('circle', 'cir').replace('centre', 'ctr') \
               .replace('corner', 'cor').replace('village', 'vlg')

def _get_station_id(station):
    with open ('stops.json') as stops_file:
        stop_data = json.load(stops_file)

    if station not in stop_data:
        return None
        print "Station not found"
        raise ValueError("Station %s not found. You Suck." % station)
    else:
        return stop_data[station]

def _lines_from_routes_data(data):
    lines = []
    for mode in data['mode']:
        if mode['mode_name'] == 'Subway':
            for route in mode['route']:
                lines.append(route)
    return lines

def _load_json_file(file_name):
    with open(file_name, 'r') as f:
        return json.load(f)

def _get_transfer_list(line, file_transfers):
    for l in file_transfers:
        if l['line'] == line:
            return l['transfers']
    return None

def _create_response_message(transfer, trip, start_time, total_time, message):
    arrivals = _retrieve_schedule_by_trip(trip['trip_id'], start_time)
    for stop in arrivals['stop']:
        if stop['stop_id'] == transfer.to_id:
            f_time = datetime.datetime.fromtimestamp(trip['sch_arr_dt']).strftime(time_format)
            t_time = datetime.datetime.fromtimestamp(stop['sch_arr_dt']).strftime(time_format)

# MBTA request helper methods

def _send_request(endpoint, parameters):
    parameters['api_key'] = real_api_key
    parameters['format'] = 'json'
    base_url = 'http://realtime.mbta.com/developer/api/v2/'
    r = requests.get(base_url + endpoint, params=parameters)
    return r.json()

def _retrieve_schedule_by_stop(train_id, max_trips=3, time=None):
    payload = None
    if time == None:
        payload = {'max_time': 600, 'stop': train_id, 'max_trips': max_trips}
    else:
        payload = {'max_time': 600, 'stop': train_id, 'max_trips': max_trips, 'datetime': time}
    data = _send_request('schedulebystop', payload)
    return data

def _retrieve_routes_by_stop(stop):
    payload = {'stop': stop}
    data = _send_request('routesbystop', payload)
    return data

def _retrieve_stops_by_route(route):
    payload = {'route': route}
    data = _send_request('stopsbyroute', payload)
    return data

def _retrieve_schedule_by_trip(trip, time=None):
    payload = None
    if time == None:
        payload = {'trip': trip}
    else:
        payload = {'trip': trip, 'datetime': time}
    data = _send_request('schedulebytrip', payload)
    return data

# classes
class TransferChain:
    def __init__(self):
        self.transfers = []
        self.tries = 0

    def add_transfer(self, _from, _from_id, _from_name, to, to_id, to_name, line):
        self.transfers.append(Transfer(_from, _from_id, _from_name, to, to_id, to_name, line))

    def contains_already(self, station, line):
        for transfer in self.transfers:
            if transfer.line == line or transfer.to == station:
                return True
        return False

class Transfer:
    def __init__(self, _from, _from_id, _from_name, to, to_id, to_name, line):
        self._from = _from
        self._from_id = _from_id
        self._from_name = _from_name
        self.to = to
        self.to_id = to_id
        self.to_name = to_name
        self.line = line

class TransferMessage:
    def __init__(self):
        self.message = ''
        self.total_time = 0
        self.time = None

#if __name__ == '__main__':
#    get_from_to_data('ruggles', 'mit')