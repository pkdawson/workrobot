import os
from racetime_bot import Bot, RaceHandler
import aiohttp
import racedata
import logging
from datetime import datetime, timedelta
import json
import asyncio
from functools import partial
from babel.dates import format_timedelta
from roll_seed import roll_race
from common import *
from dotenv import load_dotenv

load_dotenv()


def format_td(td):
    return format_timedelta(td, locale="en_US", granularity="minute")


class RTHandler(RaceHandler):
    SEED_ROLL_TIME = timedelta(minutes=15)
    REMINDER_TIME = timedelta(minutes=5)
    REMINDER2_TIME = timedelta(minutes=1)
    LATE_RACE_TIME = timedelta(minutes=1)

    def __init__(self, scheduler, **kwargs):
        self.scheduler = scheduler
        self.logger = logging.getLogger("workrobot")
        super().__init__(**kwargs)

    def all_ready(self):
        for entrant in self.data.get("entrants"):
            if entrant["status"]["value"] != "ready":
                return False
        return True

    async def begin(self):
        tstr = self.race["datetime"]
        self.logger.info(f"Begin handler for {tstr}")
        # await self.add_monitor(os.getenv('RACETIME_ME'))
        self.dt = to_datetime(tstr)
        delta = self.dt - datetime.now()
        msg = f"The race will start in {format_td(delta)}."
        if self.race.get("settings_preset"):
            msg += f" A seed will be rolled {format_td(self.SEED_ROLL_TIME)} before the start."
            run_date = self.dt - self.SEED_ROLL_TIME
            self.scheduler.add_job(self.task_roll_seed, "date", run_date=run_date)
        else:
            msg += " A seed will NOT be automatically rolled."
        await self.send_message(msg)

        run_date = self.dt - self.REMINDER_TIME
        self.scheduler.add_job(self.task_remind, "date", run_date=run_date)
        run_date = self.dt - self.REMINDER2_TIME
        self.scheduler.add_job(self.task_remind, "date", run_date=run_date)
        run_date = self.dt
        self.scheduler.add_job(self.task_start_race, "date", run_date=run_date)

    async def task_roll_seed(self):
        tstr = self.race["datetime"]
        self.logger.info(f"Rolling seed for {tstr}")
        await self.send_message("Generating seed, please wait...")
        try:
            url, hash = await roll_race(self.race)
            await self.send_message(f"{url} ({hash})")
            await self.set_bot_raceinfo(f"{url} ({hash})")
        except Exception as e:
            await self.send_message(f"ERROR: {e}")
            self.logger.error(f"{self.data['name']} Exception rolling seed: {e}")

    async def task_remind(self):
        delta = self.dt - datetime.now()
        await self.send_message(f"The race will start in {format_td(delta)}.")

    async def task_start_race(self):
        if len(self.data["entrants"]) < 2:
            await self.send_message("Not enough entrants.")
            return

        if self.all_ready():
            await self.force_start()
        else:
            await self.send_message("@unready please ready")
            await self.send_message(
                f"The race will start shortly after everyone is ready."
            )
            run_date = datetime.now() + self.LATE_RACE_TIME
            self.scheduler.add_job(self.task_late_start, "date", run_date=run_date)

    async def task_late_start(self):
        if self.all_ready():
            await self.force_start()
        else:
            run_date = datetime.now() + self.LATE_RACE_TIME
            self.scheduler.add_job(self.task_late_start, "date", run_date=run_date)


class RTBot(Bot):
    def __init__(self, scheduler, *args, **kwargs):
        self.racetime_host = os.getenv("RACETIME_HOST")
        self.racetime_secure = True if self.racetime_host == "racetime.gg" else False
        self.racetime_goal = os.getenv("RACETIME_GOAL")
        self.room_names = set()
        self.scheduler = scheduler
        super().__init__(*args, **kwargs)

    def get_handler_class(self):
        return RTHandler

    def get_handler_kwargs(self, *args, **kwargs):
        return {
            **super().get_handler_kwargs(*args, **kwargs),
            "scheduler": self.scheduler,
        }

    async def post(self, endpoint, data):
        url = self.http_uri(f"/o/{self.category_slug}/{endpoint}")
        h = {
            "Authorization": "Bearer " + self.access_token,
        }
        async with aiohttp.request(
            method="post", url=url, headers=h, raise_for_status=True, data=data
        ) as resp:
            return resp

    async def get(self, endpoint):
        url = self.http_uri(f"/o/{self.category_slug}/{endpoint}")
        h = {
            "Authorization": "Bearer " + self.access_token,
        }
        async with aiohttp.request(
            method="get", url=url, headers=h, raise_for_status=True
        ) as resp:
            return resp

    async def join_room(self, race, name, data_url):
        def done(task_name, *args):
            del self.handlers[task_name]

        try:
            async with aiohttp.request(
                method="get",
                url=self.http_uri(data_url),
                raise_for_status=True,
            ) as resp:
                race_data = json.loads(await resp.read())
        except Exception as e:
            self.logger.error(
                "Fatal error when attempting to retrieve summary data.", exc_info=True
            )
            raise e
        handler = self.create_handler(race_data)
        handler.race = race
        self.handlers[name] = self.loop.create_task(handler.handle())
        self.handlers[name].add_done_callback(partial(done, name))

    async def create_room(self, race):
        d = {
            "goal": race.get("goal", self.racetime_goal),
            "team_race": race.get("team", False),
            "invitational": False,
            "unlisted": False,
            "info_user": f"VARIA Weekly - {race['desc']}",
            "info_bot": "",
            "require_even_teams": False,
            "start_delay": 15,
            "time_limit": 24,
            "time_limit_auto_complete": False,
            "streaming_required": self.racetime_secure,
            "auto_start": False,
            "allow_comments": True,
            "hide_comments": True,
            "allow_prerace_chat": True,
            "allow_midrace_chat": True,
            "allow_non_entrant_chat": True,
            "chat_message_delay": 0,
        }

        resp = await self.post("startrace", d)
        if resp:
            name = resp.headers["Location"][1:]
            data_url = f"/{name}/data"
            self.room_names.add(name)
            self.logger.info(f"Opened {name}")
            await self.join_room(race, name, data_url)
            return name

    def should_handle(self, race_data):
        return False
