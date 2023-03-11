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
