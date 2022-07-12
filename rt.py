import os
from racetime_bot import Bot, RaceHandler
import aiohttp
import racedata
import logging
from datetime import datetime, timedelta
from common import *
from dotenv import load_dotenv
load_dotenv()


class RTHandler(RaceHandler):
    def __init__(self, scheduler, next_race, **kwargs):
        self.scheduler = scheduler
        self.tstr = next_race
        self.logger = logging.getLogger('workrobot')
        super().__init__(**kwargs)

    async def begin(self):
        self.logger.info(f'Begin handler for {self.tstr}')
        await self.send_message(f'The race will start in 30 minutes. A seed will be rolled 15 minutes before that.')

        dt = datetime.fromisoformat(self.tstr).replace(tzinfo=RACETZ)
        self.scheduler.add_job(self.roll_seed, 'date', run_date=dt -
                               timedelta(minutes=15), id=f'{self.tstr}:roll')

    async def roll_seed(self):
        self.logger.info(f'Rolling seed for {self.tstr}')
        rd = racedata.get(self.tstr)
        await self.send_message(str(rd))


class RTBot(Bot):
    def __init__(self, scheduler, *args, **kwargs):
        self.racetime_host = os.getenv('RACETIME_HOST')
        self.racetime_secure = True if self.racetime_host == 'racetime.gg' else False
        self.room_names = set()
        self.scheduler = scheduler
        self.next_race = None
        super().__init__(*args, **kwargs)

    def get_handler_class(self):
        return RTHandler

    def get_handler_kwargs(self, *args, **kwargs):
        next_race = self.next_race
        self.next_race = None
        return {
            **super().get_handler_kwargs(*args, **kwargs),
            'scheduler': self.scheduler,
            'next_race': next_race,
        }

    async def req(self, endpoint, data):
        url = self.http_uri(f'/o/{self.category_slug}/{endpoint}')
        h = {
            'Authorization': 'Bearer ' + self.access_token,
        }
        async with aiohttp.request(method='post', url=url, headers=h, raise_for_status=True, data=data) as resp:
            return resp

    async def create_room(self):
        d = {
            'goal': 'Beat the game',
            'team_race': False,
            'invitational': False,
            'unlisted': False,
            'info_user': '',
            'info_bot': '',
            'require_even_teams': False,
            'start_delay': 15,
            'time_limit': 24,
            'time_limit_auto_complete': False,
            'streaming_required': self.racetime_secure,
            'auto_start': False,
            'allow_comments': True,
            'hide_comments': True,
            'allow_prerace_chat': True,
            'allow_midrace_chat': True,
            'allow_non_entrant_chat': True,
            'chat_message_delay': 0,
        }

        resp = await self.req('startrace', d)
        if resp:
            name = resp.headers['Location'][1:]
            self.room_names.add(name)
            self.logger.info(f'Opened {name}')
            return name

    def should_handle(self, race_data):
        # ignore rooms not created by us
        if race_data['name'] in self.room_names:
            return super().should_handle(race_data)
        return False
