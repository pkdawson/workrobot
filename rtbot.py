import os
from dotenv import load_dotenv
load_dotenv()

from racetime_bot import Bot, RaceHandler
import logging

class WRHandler(RaceHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def begin(self):
        print('begin')
        await self.send_message('hello world')

class WRBot(Bot):
    def __init__(self, *args, **kwargs):
        self.racetime_host = os.getenv('RACETIME_HOST')
        self.racetime_secure = True if self.racetime_host == 'racetime.gg' else False
        super().__init__(*args, **kwargs)

    def get_handler_class(self):
        return WRHandler


def main():
    logger = logging.getLogger()
    bot = WRBot(
        category_slug=os.getenv('RACETIME_CAT'),
        client_id=os.getenv('RACETIME_CLIENT_ID'),
        client_secret=os.getenv('RACETIME_CLIENT_SECRET'),
        logger=logger)
    bot.run()

main()
