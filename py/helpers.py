import global_vars


# mAkE iT sPeAk LiKe ThIs
def spongify(message):
    flip_flop = True
    response = ""
    for char in message:
        if char.isalpha():
            if flip_flop is False:
                response += char.upper()
                flip_flop = True
            else:
                response += char.lower()
                flip_flop = False
        else:
            response += char
    return response


def get_name_from_iracing_id(iracing_id):
    for member in global_vars.members:
        if 'iracingCustID' in global_vars.members[member] and 'leaderboardName' in global_vars.members[member] and global_vars.members[member]['iracingCustID'] == iracing_id:
            return global_vars.members[member]['leaderboardName']
    return ""


def is_respo_driver(iracing_id):
    for member in global_vars.members:
        if 'iracingCustID' in global_vars.members[member] and global_vars.members[member]['iracingCustID'] == iracing_id:
            return True
    return False


def get_member_dict_from_first_name(member_name_from_list):
    global_vars.members_locks += 1
    for member_key in global_vars.members:
        if "leaderboardName" in global_vars.members[member_key]:
            name_split = global_vars.members[member_key]["leaderboardName"].split()
            if len(name_split) > 0 and name_split[0].lower() == member_name_from_list.lower():
                global_vars.members_locks -= 1
                return global_vars.members[member_key]

    global_vars.members_locks -= 1

    return {}


def get_member_dict_from_iracing_id(iracing_id):
    global_vars.members_locks += 1
    for member_key in global_vars.members:
        if "iracingCustID" in global_vars.members[member_key] and global_vars.members[member_key]['iracingCustID'] == iracing_id:
            return global_vars.members[member_key]

    global_vars.members_locks -= 1

    return {}


def get_member_key(member_name_from_list):
    global_vars.members_locks += 1
    for member_key in global_vars.members:
        if "leaderboardName" in global_vars.members[member_key]:
            name_split = global_vars.members[member_key]["leaderboardName"].split()
            if len(name_split) > 0 and name_split[0].lower() == member_name_from_list.lower():
                global_vars.members_locks -= 1
                return member_key

    global_vars.members_locks -= 1

    return ""
