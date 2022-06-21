from datetime import datetime, timezone, timedelta
from common import *
import time
import shelve

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from roll_seed import generate_seed
from ruamel.yaml import YAML

class Runner:
    def __init__(self):
        self.db = shelve.open('races.db')
        self.loop = asyncio.events.new_event_loop()
        self.scheduler = AsyncIOScheduler(event_loop=self.loop)

    def load_schedule(self):
        yaml = YAML(typ='safe')
        with open('data/races.yaml', 'r') as fi:
            ydat = yaml.load(fi)

        for race in ydat['races']:
            tstr = race['datetime']
            t = datetime.fromisoformat(tstr).replace(tzinfo=RACETZ)
            if tstr not in self.db:
                print('new race')
                self.db[tstr] = {'status': 'waiting'}

            print(tstr, self.db[tstr])

            # dt = t - datetime.now(timezone.utc)
            # while dt > timedelta(minutes=35):
            #     sleep_time = min(dt, timedelta(minutes=5))
            #     print(f'Next race in {dt}, sleeping for {sleep_time}')
            #     time.sleep(sleep_time.total_seconds())
            #     dt = t - datetime.now(timezone.utc)

    def run(self):
        asyncio.events.set_event_loop(self.loop)
        self.scheduler.start()

        self.scheduler.add_job(self.load_schedule)
        self.scheduler.add_job(self.load_schedule, 'interval', minutes=5, id='load_schedule')

        try:
            self.loop.run_forever()
        except:
            pass

def main():
    r = Runner()
    r.run()

main()
