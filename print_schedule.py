from ruamel.yaml import YAML
from datetime import datetime
from zoneinfo import ZoneInfo

def main():
    racetz = ZoneInfo('America/New_York')

    yaml = YAML(typ='safe')
    with open('data/races.yaml', 'r') as fi:
        ydat = yaml.load(fi)

    prev_date = None
    for race in ydat['races']:
        dt = datetime.fromisoformat(race['datetime']).replace(tzinfo=racetz)
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
