from ruamel.yaml import YAML
from datetime import datetime
from common import *

def main():
    yaml = YAML(typ='safe')
    with open('data/races.yaml', 'r') as fi:
        ydat = yaml.load(fi)

    prev_date = None
    for race in ydat['races']:
        dt = datetime.fromisoformat(race['datetime']).replace(tzinfo=RACETZ)
        ts = int(dt.timestamp())
        desc = race['desc']

        if prev_date != dt.date():
            day = dt.strftime('%A')
            print('')
            print(f'{day} <t:{ts}:d>')
        prev_date = dt.date()

        print(f'<t:{ts}:t> (<t:{ts}:R>) - {desc}')

if __name__ == '__main__':
    main()
