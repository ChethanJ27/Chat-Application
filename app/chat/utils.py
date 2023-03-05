

def createRoomId(user1_email,user2_email):
    u1_email = user1_email.replace('.', '_').replace('@', '-')
    u2_email = user2_email.replace('.', '_').replace('@', '-')
    room_id = "-".join(sorted([user1_email, user2_email]))
    return room_id