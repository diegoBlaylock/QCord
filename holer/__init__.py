from orjson.orjson import loads
from main import FILE_ROOT as root


def getjson(name):
    with open(name, "r") as file:
     
        return loads(file.read())
    
SETTINGS_JSON = getjson(f"{root}/questions/settings.json")
