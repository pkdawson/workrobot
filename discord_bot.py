import os
from dotenv import load_dotenv
load_dotenv()

import disnake
from disnake.ext import tasks

class DiscordClient(disnake.Client):
    def __init__(self, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg = msg
        self.channel_id = int(os.getenv('DISCORD_CHANNEL'))
        self.role_id = int(os.getenv('DISCORD_ROLE'))

    async def on_ready(self):
        print(f'We have logged in as {self.user}')
        chan = self.get_channel(self.channel_id)
        if chan:
            await chan.send(f'<@&{self.role_id}> {self.msg}')
            # not sure how to cleanly terminate
            await self.close()
        else:
            raise Exception("channel not found")


def send_message(msg):
    client = DiscordClient(msg)
    client.run(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    send_message('hello world')
