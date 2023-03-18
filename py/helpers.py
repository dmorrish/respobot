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


def get_name_from_iracing_id(cust_id):
    for member in global_vars.members:
        if 'iracingCustID' in global_vars.members[member] and 'leaderboardName' in global_vars.members[member] and global_vars.members[member]['iracingCustID'] == cust_id:
            return global_vars.members[member]['leaderboardName']
    return ""
