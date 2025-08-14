def arrayToString(arr: list):
    return ",".join(arr) if arr else ""

def stringToArray(string: str):
    return string.split(",") if string else []