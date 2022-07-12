from ruamel.yaml import YAML
from datetime import datetime
from common import *


def _load_yaml():
    yaml = YAML(typ='safe')
    with open('data/races.yaml', 'r') as fi:
        ydat = yaml.load(fi)
        return ydat


def get(tstr):
    ydat = _load_yaml()
    for race in ydat['races']:
        if tstr == race['datetime']:
            return race
    return None


def get_next():
    ydat = _load_yaml()
    now = datetime.now(RACETZ)

    # TODO: sort first, just in case
    for race in ydat['races']:
        dt = datetime.fromisoformat(race['datetime']).replace(tzinfo=RACETZ)
        if dt > now:
            return race

    raise Exception('no future races scheduled')
