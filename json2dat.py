import re


def encode_data_to_dat(data):
    output = ""
    # Header
    # Byte size (no idea what it should be)
    output += format_number_output(0) + "\n"
    output += format_number_output(data['header']['number_of_objects']) + "\n"
    output += format_number_output(data['header']['number_of_actions']) + "\n"
    output += format_number_output(data['header']['number_of_words']) + "\n"
    output += format_number_output(data['header']['number_of_rooms']) + "\n"
    output += format_number_output(data['header']
                                   ['max_objects_carried']) + "\n"
    output += format_number_output(data['header']['starting_room']) + "\n"
    output += format_number_output(data['header']
                                   ['number_of_treasures']) + "\n"
    output += format_number_output(data['header']['word_length']) + "\n"
    output += format_number_output(data['header']['time_limit']) + "\n"
    output += format_number_output(data['header']['number_of_messages']) + "\n"
    output += format_number_output(data['header']['treasure_room_id']) + "\n"

    # Actions
    for action_index, _ in enumerate(data['action']):

        # Precondition
        precondition = 150 * data['action'][action_index]['precondition'][0] + \
            data['action'][action_index]['precondition'][1]
        output += format_number_output(precondition) + "\n"

        # Condition
        number_of_condition_code = {"parameter": 0,
                                    "carried": 1,
                                    "here": 2,
                                    "present": 3,
                                    "at": 4,
                                    "not_here": 5,
                                    "not_carried": 6,
                                    "not_at": 7,
                                    "flag": 8,
                                    "not_flag": 9,
                                    "loaded": 10,
                                    "not_loaded": 11,
                                    "not_present": 12,
                                    "exists": 13,
                                    "not_exists": 14,
                                    "counter_le": 15,
                                    "counter_gt": 16,
                                    "not_moved": 17,
                                    "moved": 18,
                                    "counter_eq": 19, }
        for condition_index, condition in enumerate(data['action'][action_index]['condition']):
            condition_argument = data['action'][action_index]['condition_argument'][condition_index]
            if condition_argument < 0:  # condition argument should never be < 0
                condition_argument = 0
            encoded_condition = number_of_condition_code[condition] + \
                20*condition_argument
            output += format_number_output(encoded_condition) + "\n"

        # Command
        number_of_command_code = {"get": 52,
                                  "drop": 53,
                                  "goto": 54,
                                  "destroy": 55,
                                  "set_dark": 56,
                                  "clear_dark": 57,
                                  "set_flag": 58,
                                  "clear_flag": 60,
                                  "die": 61,
                                  "put": 62,
                                  "game_over": 63,
                                  "look": 64,
                                  "score": 65,
                                  "inventory": 66,
                                  "set_flag0": 67,
                                  "clear_flag0": 68,
                                  "refill_lamp": 69,
                                  "clear": 70,
                                  "save_game": 71,
                                  "swap": 72,
                                  "continue": 73,
                                  "superget": 74,
                                  "put_with": 75,
                                  "dec_counter": 77,
                                  "print_counter": 78,
                                  "set_counter": 79,
                                  "swap_room": 80,
                                  "select_counter": 81,
                                  "add_to_counter": 82,
                                  "subtract_from_counter": 83,
                                  "print_noun": 84,
                                  "println_noun": 85,
                                  "println": 86,
                                  "swap_specific_room": 87,
                                  "pause": 88,
                                  "no_operation": 0, }
        command_code_list = []
        for command in data['action'][action_index]['command']:
            m = re.search('message_(\d+)', command)
            if m:
                message_id = int(m.group(1)) + 1
                if message_id < 52:
                    command_code_list.append(message_id)
                else:
                    command_code_list.append(message_id+50)
            else:
                command_code_list.append(number_of_command_code[command])
        output += format_number_output(
            150*command_code_list[0] + command_code_list[1]) + "\n"
        output += format_number_output(
            150*command_code_list[2] + command_code_list[3]) + "\n"

    # Vocabulary
    if len(data['verb']) > len(data['noun']):
        vocabulary_length = len(data['verb'])
        difference = len(data['verb']) - len(data['noun'])
        data['noun'] += [''] * difference
    else:
        vocabulary_length = len(data['noun'])
        difference = len(data['noun']) - len(data['verb'])
        data['verb'] += [''] * difference
    for vocabulary_index in range(vocabulary_length):
        output += "\"%s\"" % data['verb'][vocabulary_index] + "\n"
        output += "\"%s\"" % data['noun'][vocabulary_index] + "\n"

    # Room
    for room in data['room']:
        for exit in room['exit']:
            output += format_number_output(exit) + "\n"
        description = room['description']
        m = re.search("^I'm in a ([\s\S]*)", description)
        if m:
            output += "\"%s\"" % m.group(1) + "\n"
        else:
            if len(description) > 0:
                output += "\"*%s\"" % description + "\n"
            else:
                output += "\"\"" + "\n"

    # Message
    output += "\"\"" + "\n"  # The initial empty message
    for message in data['message']:
        output += "\"%s\"" % message.replace('"', '`') + "\n"

    # Object
    for obj in data['object']:
        if len(obj['noun']) > 0:
            obj_description = obj['description'] + "/%s/" % obj['noun']
        else:
            obj_description = obj['description']
        output += "\"%s\" %d " % (obj_description.replace(
            '"', '`'), obj['starting_location']) + "\n"

    # Action titles
    for action in data['action']:
        output += "\"%s\"" % action['title'].replace('"', '`') + "\n"

    # Trailer
    output += format_number_output(data['header']['adventure_version']) + "\n"
    output += format_number_output(data['header']['adventure_number']) + "\n"
    # Don't feel like computing this, so let's ignore it
    output += format_number_output(0)

    return output


def format_number_output(number):
    if number < 0:
        return "%d " % number
    else:
        return " %d " % number
