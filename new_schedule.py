import sys
import ruamel
from ruamel.yaml import YAML
from datetime import datetime, date, time
from common import *
import fileinput


class NonAliasingRTRepresenter(ruamel.yaml.RoundTripRepresenter):
    def ignore_aliases(self, data):
        return True


def main():
    out = {'races': []}

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
                    r = {'datetime': dt.strftime('%Y-%m-%d %H:%M')}
                    for k in w.keys():
                        if k not in ('isoweekday', 'time', 'msg'):
                            r[k] = w[k]
                    kw = dt.isocalendar().week

                    sunday = d.isoweekday() == 7
                    casual = r['skills_preset'] == 'casual'

                    # alternate simple and complex, and do the opposite on Sunday
                    simple = True
                    if (kw % 2 == 0 and casual) or (kw % 2 != 0 and not casual):
                        simple = False
                    if sunday:
                        simple = not simple

                    if simple:
                        r['desc'] += ' - Simple'
                    else:
                        r['desc'] += ' - Complex'
                    out['races'].append(r)

            day = day + 1

    except ValueError:
        pass

    # ugly hack
    replace_last = 'Casual - Complex' if month % 2 == 0 else 'Hard - Complex'
    for i, obj in reversed(list(enumerate(out['races']))):
        if obj['desc'] == replace_last:
            out['races'][i]['desc'] = obj['desc'].replace('Complex', 'Mystery')
            break

    yout = YAML()
    yout.default_flow_style = False
    yout.version = (1, 2)
    yout.indent(mapping=2, sequence=4, offset=2)
    yout.Representer = NonAliasingRTRepresenter
    with open('data/races-new.yaml', 'w') as fout:
        yout.dump(out, fout)

    # add whitespace
    with fileinput.FileInput('data/races-new.yaml', inplace=True) as f:
        for line in f:
            if line.startswith('  -') and f.lineno() > 4:
                print()
            print(line, end='')


if __name__ == '__main__':
    main()
