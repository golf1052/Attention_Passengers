import message_parser
import mbta
import passengers

def test_parser_good():
    # good inputs
    message_info = _create_message('ruggles inbound')
    result = message_parser.parse_message_body(message_info)
    assert result.return_type == 'dir'
    assert len(result.result) == 2
    assert result.result[0] == 'inbound'
    assert result.result[1] == 'ruggles'
    message_info = _create_message('longwood medical area out')
    result = message_parser.parse_message_body(message_info)
    assert result.return_type == 'dir'
    assert len(result.result) == 2
    assert result.result[0] == 'out'
    assert result.result[1] == 'longwood medical area'
    message_info = _create_message('ruggles to dtx')
    result = message_parser.parse_message_body(message_info)
    assert result.return_type == 'dest'
    assert len(result.result) == 2
    assert result.result[0] == 'ruggles'
    assert result.result[1] == 'dtx'
    message_info = _create_message('kendall/mit 2 south station')
    result = message_parser.parse_message_body(message_info)
    assert result.return_type == 'dest'
    assert len(result.result) == 2
    assert result.result[0] == 'kendall/mit'
    assert result.result[1] == 'south station'
    message_info = _create_message('chestnut hill ave x longwood medical area')
    result = message_parser.parse_message_body(message_info)
    assert result.return_type == 'dest'
    assert len(result.result) == 2
    assert result.result[0] == 'chestnut hill ave'
    assert result.result[1] == 'longwood medical area'

def test_parser_bad():
    # bad inputs
    message_info = _create_message('rugglesinbound')
    result = message_parser.parse_message_body(message_info)
    assert result.return_type == 'other'
    assert len(result.result) == 1
    assert result.result[0] == 'rugglesinbound'
    message_info = _create_message('inbound what is station')
    result = message_parser.parse_message_body(message_info)
    assert result.return_type == 'dir'
    assert len(result.result) == 2
    assert result.result[0] == 'station'
    assert result.result[1] == 'inbound what is'
    message_info = _create_message('ruggles2 dtx')
    result = message_parser.parse_message_body(message_info)
    assert result.return_type == 'dir'
    assert len(result.result) == 2
    assert result.result[0] == 'dtx'
    assert result.result[1] == 'ruggles2'

def _create_message(message):
    return passengers.MessageInfo(None, None, message, 0, None, None, None, None, '')
