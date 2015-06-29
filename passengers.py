from passenger import Passenger

class MessageInfo:
    def __init__(self, sid, number, body, num_media, city, state, zip, country, status):
        self.sid = sid
        self.number = number
        self.body = body.lower().strip()
        self.num_media = num_media
        self.city = city
        self.state = state
        self.zip = zip
        self.country = country
        self.status = status

def load_message_info(message):
    return MessageInfo(message.sid, message.from_,
                       message.body.lower(), message.num_media,
                       None, None, None, None,
                       message.status)

def check_for_user(message_info):
    results = Passenger.Query.filter(number=message_info.number)
    if len(results) == 0:
        return create_user(message_info)
    else:
        if len(results) == 1:
            return results[0]
        else:
            return None

def create_user(message_info):
    messages = []
    favorites = []
    user = Passenger(
        number=message_info.number, city=message_info.city,
        state=message_info.state, zip=message_info.zip,
        country=message_info.country, messages=messages,
        favorites=favorites, fState="None",
        fKeyword="", timeFormat="12h")
    user.save()
    return user
