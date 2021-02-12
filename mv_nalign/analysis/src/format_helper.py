# group by timestamp
def format_objects(objs, key):
    if not len(objs):
        return []
    formatted = {}
    cursor = -1
    timestamp = []
    for val in objs:
        if cursor != val["Timestamp"]:
            if cursor != -1:
                formatted[cursor] = timestamp
            cursor = val["Timestamp"]
            timestamp = [val[key]]
        else:
            timestamp.append(val[key])
    # Last one
    formatted[cursor] = timestamp
    return formatted
