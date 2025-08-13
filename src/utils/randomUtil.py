import random

CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
def randomString(length):
    result = ""
    for i in range(length):
        result += random.choice(CHARSET)
    return result