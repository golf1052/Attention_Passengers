# Parse the received text body (and the phone number) into something useful...
def parse_message_body(message_info):
    lower_case = message_info.body.lower().strip()
    parsed_list = lower_case.split(' ')
    for i in range(len(parsed_list)):
        if _is_a_to(parsed_list[i]):
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
            return ParserType('dest', [from_station, to_station])
    if (len(parsed_list) >= 2):
        station = join_strings(parsed_list[0:-1])
        direction = parsed_list[-1]
        return ParserType('dir', [direction, station])
    return ParserType('other', [lower_case])

def _is_a_to(s):
    s = s.lower().strip()
    return s == 'to' or s == '-' or s == 'x' or s == 't' or s == '2'

def get_stations(message_info):
    lower_case = message_info.body.lower().strip()
    parsed_list = lower_case.split(' ')
    for i in range(len(parsed_list)):
        if _is_a_to(parsed_list[i]):
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
           keyword == 'cancel' or keyword == '12' or keyword == '24'

def join_strings(strings):
    output = ''
    for i in range(len(strings)):
        if i == (len(strings) - 1):
            output += strings[i]
        else:
            output += strings[i] + ' '
    return output

class ParserType:
    def __init__(self, return_type, result):
        self.return_type = return_type
        self.result = result
