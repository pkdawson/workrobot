from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import time
import shelve

from gen import get_next_race

class Runner:
    def __init__(self):
        self.racetz = ZoneInfo('America/New_York')
        self.db = shelve.open('races.db')

    def run(self):
        race = get_next_race()

        tstr = race['datetime']
        t = datetime.fromisoformat(tstr).replace(tzinfo=self.racetz)
        if tstr not in self.db:
            print('new race')
            self.db[tstr] = {'status': 'waiting'}

        dt = t - datetime.now(timezone.utc)
        while dt > timedelta(minutes=35):
            sleep_time = min(dt, timedelta(minutes=5))
            print(f'Next race in {dt}, sleeping for {sleep_time}')
            time.sleep(sleep_time.total_seconds())
            dt = t - datetime.now(timezone.utc)

def main():
    r = Runner()
    r.run()

main()
