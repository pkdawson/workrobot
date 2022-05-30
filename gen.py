import sys
sys.path += ['pyz3r']
from pyz3r.smvaria import SuperMetroidVaria
import asyncio, asyncio.events

sys.path += ['RandomMetroidSolver']
from rom.ips import IPS_Patch
from base64 import b64decode
import io

from rominfo import get_hash

from ruamel.yaml import YAML

async def generate_seed(smv):
    smv.settings = await smv.get_settings()
    data = await smv.generate_game()

    if data['status'] != 'OK':
        print(data['errorMsg'])
        raise Exception()

    with open('temp.ips', 'wb') as fout:
        fout.write(b64decode(data['ips']))

    ips = IPS_Patch.load('temp.ips')

    old = bytes([0xFF]*3*1024*1024)
    new = ips.apply(old)
    
    del data['ips']
    print(data)
    hash = get_hash(io.BytesIO(new))

    if data['errorMsg'] != '':
        print(f"Warnings: {data['errorMsg']}")

    print(f"{smv.baseurl}/customizer/{data['seedKey']} ({hash})")


def main():
    yaml = YAML(typ='safe')
    with open('data/races.yaml', 'r') as fi:
        ydat = yaml.load(fi)

    race = ydat['races'][1]

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
    loop.run_until_complete(generate_seed(smv))

main()
