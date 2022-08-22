import disnake
import os
import logging
from dotenv import load_dotenv
load_dotenv()


class DiscordClient(disnake.Client):
    def __init__(self, *args, **kwargs):
        self.channel_id = int(os.getenv('DISCORD_CHANNEL'))
        self.role_id = int(os.getenv('DISCORD_ROLE'))
        self.logger = logging.getLogger('workrobot')
        super().__init__(activity=self.get_activity(), *args, **kwargs)

    def get_activity(self):
        return disnake.Game('on Saturday')

    async def on_ready(self):
        self.logger.info(f'Discord client logged in as {self.user}')

    async def send_announcement(self, msg):
        await self.wait_until_ready()
        chan = self.get_channel(self.channel_id)
        if chan:
            await chan.send(f'<@&{self.role_id}> {msg}')
        else:
            raise Exception("channel not found")

    async def dm(self, userid, msg):
        await self.wait_until_ready()
        user = await self.fetch_user(userid)
        if user:
            await user.send(msg)


if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    import asyncio
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.events.new_event_loop()
    asyncio.events.set_event_loop(loop)
    dc = DiscordClient()

    loop.create_task(dc.start(os.environ.get("DISCORD_TOKEN")))
    loop.run_forever()
