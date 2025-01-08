import json

def valueGet(key,defaultValue):
    try:
        RetrievedValue = data[key]
        return {"RetrievedValue": RetrievedValue}
    except Exception as e:
        return{}
    

data = {
    "value1":"result1",
    "value2":"result2",
    "value3":"result3",
    "value4":"result4",
    }

data2 = {"value5":"result5"}

data.update(data2)

data["value6"]="result6"

data["value6"]="result60"

data3 = {
    "value1":"result10",
    "value2":"result20",
    "value3":"result30",
    "value4":"result40",
    "value7":"result70",
    }

data.update(data3)

print(valueGet("value8","default"))

if "value8" in data:
    print("Value8 found")
    data.pop('value8', None)
else:
    print("Value8 NOT found")
    

print(data)