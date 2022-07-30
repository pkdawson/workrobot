import sys
sys.path += ['RandomMetroidSolver']  # nopep8
from common import *
from rominfo import get_hash
import io
from base64 import b64decode
from rom.ips import IPS_Patch
import os
from pyz3r.smvaria import SuperMetroidVaria
import asyncio
import asyncio.events
import racedata
import logging
from tenacity import retry, stop_after_attempt


@retry(stop=stop_after_attempt(3))
async def generate_seed(smv):
    logger = logging.getLogger('workrobot')
    smv.settings = await smv.get_settings()
    data = await smv.generate_game()

    if data['status'] != 'OK':
        raise Exception(data['errorMsg'])

    with open('temp.ips', 'wb') as fout:
        fout.write(b64decode(data['ips']))

    ips = IPS_Patch.load('temp.ips')

    old = bytes([0xFF]*3*1024*1024)
    new = ips.apply(old)

    del data['ips']
    logger.info(data)
    hash = get_hash(io.BytesIO(new))

    if data['errorMsg'] != '':
        logger.warning(f"Warnings: {data['errorMsg']}")

    os.remove('temp.ips')
    return (f"{smv.baseurl}/customizer/{data['seedKey']}", hash)


def main():
    async def roll(smv):
        url, hash = await generate_seed(smv)
        print(f"{url} ({hash})")

    if len(sys.argv) > 1:
        race = racedata.get(sys.argv[1])
    else:
        race = racedata.get_next()

    smv = SuperMetroidVaria(
        skills_preset=race['skills_preset'],
        settings_preset=race['settings_preset'],
        race=True,
        baseurl=race['baseurl'] if 'baseurl' in race else 'https://randommetroidsolver.pythonanywhere.com',
        username=None,
        password=None,
        settings_dict=race['custom_settings'] if 'custom_settings' in race else None
    )
    loop = asyncio.events.new_event_loop()
    asyncio.events.set_event_loop(loop)
    loop.run_until_complete(roll(smv))


if __name__ == '__main__':
    main()
