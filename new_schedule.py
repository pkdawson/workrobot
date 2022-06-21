import sys
from ruamel.yaml import YAML
from datetime import datetime, date, time
from common import *

def main():
    out = {'races' : []}

    yaml = YAML(typ='safe')
    with open('data/common.yaml', 'r') as fi:
        ydat = yaml.load(fi)

    d = date.today()
    year = d.year
    month = d.month + 1
    if month == 13:
        # skip Smarch
        year = year + 1
        month = 1
    day = 1

    try:
        while True:
            d = date(year, month, day)
            for w in ydat['weekly']:
                if w['isoweekday'] == d.isoweekday():
                    t = time.fromisoformat(w['time'])
                    dt = datetime.combine(d, t, tzinfo=RACETZ)
                    r = {'datetime' : dt.strftime('%Y-%m-%d %H:%M')}
                    for k in w.keys():
                        if k not in ('isoweekday', 'time', 'msg'):
                            r[k] = w[k]
                    out['races'].append(r)

            day = day + 1

    except ValueError:
        pass

    yout = YAML()
    yout.default_flow_style = False
    yout.version = (1, 2)
    yout.indent(mapping=2, sequence=4, offset=2)
    with open('data/races-new.yaml', 'w') as fout:
        yout.dump(out, fout)

if __name__ == '__main__':
    main()
