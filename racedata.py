from ruamel.yaml import YAML


def get(tstr):
    yaml = YAML(typ='safe')
    with open('data/races.yaml', 'r') as fi:
        ydat = yaml.load(fi)
    for race in ydat['races']:
        if tstr == race['datetime']:
            return race
    return None
