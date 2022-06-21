import os
from dotenv import load_dotenv
load_dotenv()

import disnake

class DiscordClient(disnake.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_id = int(os.getenv('DISCORD_CHANNEL'))
        self.role_id = int(os.getenv('DISCORD_ROLE'))

    async def on_ready(self):
        print(f'Discord client logged in as {self.user}')

    async def send_message(self, msg):
        await self.wait_until_ready()
        chan = self.get_channel(self.channel_id)
        if chan:
            await chan.send(f'<@&{self.role_id}> {msg}')
        else:
            raise Exception("channel not found")
