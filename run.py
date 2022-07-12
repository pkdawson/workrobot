import os
from datetime import datetime, timedelta, time
from common import *
import shelve

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from roll_seed import generate_seed
from ruamel.yaml import YAML

from dc import DiscordClient
from rt import RTBot
import logging
import racedata
from enum import Enum


class Todo(Enum):
    # the bot's to-do list
    WAITING = 0
    OPEN_ROOM = 100
    ROLL_SEED = 110
    START_RACE = 120
    DISCORD_ANNOUNCE = 200


class Runner:
    def __init__(self):
        self.loop = asyncio.events.new_event_loop()
        asyncio.events.set_event_loop(self.loop)

        self.db = shelve.open('races.db', writeback=True)
        self.scheduler = AsyncIOScheduler(event_loop=self.loop)
        self.dc = DiscordClient()
        logging.basicConfig(level=logging.WARNING, handlers=[
                            logging.StreamHandler()])
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger('workrobot')
        self.logger.setLevel(logging.INFO)

    async def load_schedule(self):
        ydat = racedata._load_yaml()

        for race in ydat['races']:
            tstr = race['datetime']
            if tstr not in self.db:
                self.logger.info(f'new race {tstr}')
                self.db[tstr] = set()

        now = datetime.now(RACETZ)
        for tstr in self.db:
            t = datetime.fromisoformat(tstr).replace(tzinfo=RACETZ)
            if t > now:
                dt = t - now
                if dt < timedelta(minutes=60):
                    if self.db[tstr] == 'waiting':
                        self.logger.info('race soon')
                        room_time = t - timedelta(minutes=30)
                        self.scheduler.add_job(self.open_raceroom, 'date', run_date=room_time, args=[
                                               tstr], id=f'{tstr}:open')
                        self.db[tstr] = 'opening'

        self.db.sync()

    async def open_raceroom(self, tstr):
        # we really don't need to worry about starting more than one race at a time,
        # but let's be safe anyway
        async with self.lock:
            self.rtbot.next_race = tstr
            name = await self.rtbot.create_room()
            self.logger.info(f'Opened {name} for race at {tstr}')

            # wait for handler to start and grab the next_race
            while self.rtbot.next_race is not None:
                await asyncio.sleep(1)
        await self.announce_raceroom(tstr, name)

    def get_weekly_info(self, dt):
        yaml = YAML(typ='safe')
        with open('data/common.yaml', 'r') as fi:
            ydat = yaml.load(fi)

        for w in ydat['weekly']:
            if dt.isoweekday() == w['isoweekday'] and dt.time() == time.fromisoformat(w['time']):
                return w
        else:
            return {'msg': 'race starts {reltime} ({desc})'}

    async def announce_raceroom(self, tstr, name):
        dt = datetime.fromisoformat(tstr).replace(tzinfo=RACETZ)
        w = self.get_weekly_info(dt)
        ts = int(dt.timestamp())
        reltime = f'<t:{ts}:R>'

        r = racedata.get(tstr)
        await self.dc.send_message(w['msg'].format(reltime=reltime, desc=r['desc']) + ' ' + self.rtbot.http_uri(f'/{name}'))

    def run(self):
        self.rtbot = RTBot(
            self.scheduler,
            category_slug=os.getenv('RACETIME_CAT'),
            client_id=os.getenv('RACETIME_CLIENT_ID'),
            client_secret=os.getenv('RACETIME_CLIENT_SECRET'),
            logger=logging.getLogger('racetime'))

        self.scheduler.configure(job_defaults={
            'misfire_grace_time': 10*60,  # 10 minutes
        })
        self.scheduler.start()

        self.scheduler.add_job(self.load_schedule)
        self.scheduler.add_job(
            self.load_schedule, 'interval', minutes=5, id='load_schedule')

        self.loop.create_task(self.rtbot.reauthorize())
        self.loop.create_task(self.rtbot.refresh_races())
        self.loop.create_task(self.dc.start(os.getenv('DISCORD_TOKEN')))

        self.loop.run_forever()


if __name__ == '__main__':
    try:
        r = Runner()
        r.run()
    finally:
        r.db.close()
