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
