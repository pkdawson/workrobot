import os
from datetime import datetime, timezone, timedelta
from common import *
import time
import shelve

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from roll_seed import generate_seed
from ruamel.yaml import YAML

from discord_bot import DiscordClient
from rtbot import WRBot
import logging
import aiohttp


class Runner:
    def __init__(self):
        self.db = shelve.open('races.db')
        self.loop = asyncio.events.new_event_loop()
        self.scheduler = AsyncIOScheduler(event_loop=self.loop)
        self.dc = DiscordClient()
        self.logger = logging.getLogger()
        # logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()])
        self.lock = asyncio.Lock()

    async def load_schedule(self):
        yaml = YAML(typ='safe')
        with open('data/races.yaml', 'r') as fi:
            ydat = yaml.load(fi)

        for race in ydat['races']:
            tstr = race['datetime']
            if tstr not in self.db:
                print('new race')
                self.db[tstr] = 'waiting'

        now = datetime.now(timezone.utc)
        for tstr in self.db:
            t = datetime.fromisoformat(tstr).replace(tzinfo=RACETZ)
            if t > now:
                dt = t - now
                if dt < timedelta(minutes=60):
                    if self.db[tstr] == 'waiting':
                        print('race soon')
                        print(tstr)
                        room_time = t - timedelta(minutes=30)
                        self.scheduler.add_job(self.open_raceroom, 'date', run_date=room_time, args=[
                                               tstr], id=f'{tstr}:open')
                        self.db[tstr] = 'opening'
                        await self.open_raceroom(tstr)
                        await self.announce_raceroom(tstr)

    async def open_raceroom(self, tstr):
        # we really don't need to worry about starting more than one race at a time,
        # but let's be safe anyway
        async with self.lock:
            self.rtbot.next_race = tstr
            name = await self.rtbot.startrace()
            print(f'Opened {name} for race at {tstr}')

            # wait for handler to start and grab the next_race
            while self.rtbot.next_race is not None:
                await asyncio.sleep(1)

    def get_weekly_info(self, dt):
        yaml = YAML(typ='safe')
        with open('data/common.yaml', 'r') as fi:
            ydat = yaml.load(fi)

    async def announce_raceroom(self, tstr):
        dt = datetime.fromisoformat(tstr).replace(tzinfo=RACETZ)
        w = self.get_weekly_info(dt)
        print(dt.isoweekday())
        print(dt.time())

    async def discord_loop(self):
        await self.dc.start(os.getenv('DISCORD_TOKEN'))

    async def dctest(self):
        await self.dc.wait_until_ready()
        await self.dc.send_message('hello send_message')

    async def racetime_loop(self):
        await self.rtbot.reauthorize()

    async def racetime_refresh(self):
        await self.rtbot.refresh_races()

    def run(self):
        asyncio.events.set_event_loop(self.loop)
        self.rtbot = WRBot(
            self.scheduler,
            category_slug=os.getenv('RACETIME_CAT'),
            client_id=os.getenv('RACETIME_CLIENT_ID'),
            client_secret=os.getenv('RACETIME_CLIENT_SECRET'),
            logger=self.logger)

        self.scheduler.start()

        self.scheduler.add_job(self.load_schedule)
        self.scheduler.add_job(
            self.load_schedule, 'interval', minutes=5, id='load_schedule')
        self.scheduler.add_job(self.discord_loop)
        self.scheduler.add_job(self.racetime_loop)
        self.scheduler.add_job(self.racetime_refresh)

        try:
            self.loop.run_forever()
        except:
            pass


def main():
    r = Runner()
    r.run()


main()
