import os
from datetime import datetime, timedelta, time
from common import *
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from ruamel.yaml import YAML
from dc import DiscordClient
from rt import RTBot
import logging
import racedata
import argparse


class ErrorHandler(logging.Handler):
    def __init__(self, dc):
        self.dc = dc
        super().__init__()

    def emit(self, record):
        if record.levelno >= logging.ERROR and not record.module.startswith('disnake'):
            msg = self.format(record)
            loop = asyncio.events.get_event_loop()
            loop.create_task(self.dc.dm(int(os.getenv('DISCORD_ME')), msg))


class Runner:
    def __init__(self, test_race=False):
        self.test_race = test_race
        self.loop = asyncio.events.new_event_loop()
        asyncio.events.set_event_loop(self.loop)

        self.scheduler = AsyncIOScheduler(event_loop=self.loop)
        self.dc = DiscordClient()
        logging.basicConfig(level=logging.INFO, handlers=[
                            logging.StreamHandler(), ErrorHandler(self.dc)])
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger('workrobot')
        self.logger.setLevel(logging.INFO)
        self.races_scheduled = set()
        self.dbg_once = 0

    def handle_exception(self, loop, context):
        self.logger.error(context)

    async def load_schedule(self):
        self.logger.info('load_schedule')
        now = datetime.now()
        ydat = racedata._load_yaml()
        if self.test_race:
            self.test_race = False
            ydat['races'][0]['desc'] = 'TEST RACE PLEASE IGNORE'
            ydat['races'][0]['datetime'] = (
                datetime.now(RACETZ) + timedelta(minutes=21)).isoformat()

        for race in ydat['races']:
            tstr = race['datetime']
            t = to_datetime(tstr)
            if t > now:
                dt = t - now
                if dt < timedelta(minutes=60):
                    if tstr not in self.races_scheduled:
                        self.races_scheduled.add(tstr)
                        self.logger.info('race soon')
                        room_time = t - timedelta(minutes=30)
                        self.scheduler.add_job(
                            self.open_raceroom, 'date', run_date=room_time, args=[race], id=tstr)

    async def open_raceroom(self, race):
        name = await self.rtbot.create_room(race)
        self.logger.info(f"Opened {name} for race at {race['datetime']}")
        await self.announce_raceroom(race, name)

    def get_weekly_info(self, dt):
        yaml = YAML(typ='safe')
        with open('data/common.yaml', 'r') as fi:
            ydat = yaml.load(fi)

        for w in ydat['weekly']:
            if dt.isoweekday() == w['isoweekday'] and dt.time() == time.fromisoformat(w['time']):
                return w
        else:
            return {'msg': 'race starts {reltime} ({desc})'}

    async def announce_raceroom(self, race, name):
        dt = to_datetime(race['datetime'])
        w = self.get_weekly_info(dt)
        ts = int(dt.timestamp())
        reltime = f'<t:{ts}:R>'
        await self.dc.send_announcement(w['msg'].format(reltime=reltime, desc=race['desc']) + ' ' + self.rtbot.http_uri(f'/{name}'))

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

        # race schedule
        self.scheduler.add_job(self.load_schedule)
        self.scheduler.add_job(
            self.load_schedule, 'interval', minutes=5, id='load_schedule')

        # racetime
        self.loop.create_task(self.rtbot.reauthorize())

        # discord
        self.loop.create_task(self.dc.start(os.getenv('DISCORD_TOKEN')))

        self.loop.set_exception_handler(self.handle_exception)
        self.loop.run_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-race', action='store_true')
    args = parser.parse_args()
    try:
        r = Runner(test_race=args.test_race)
        r.run()
    finally:
        pass
