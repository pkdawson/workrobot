
import sys
sys.path += ['RandomMetroidSolver']
from RandomMetroidSolver.rom.rom import snes_to_pc, FakeROM

words = (
    "GEEMER",
    "RIPPER",
    "ATOMIC",
    "POWAMP",
    "SCISER",
    "NAMIHE",
    "PUROMI",
    "ALCOON",
    "BEETOM",
    "OWTCH",
    "ZEBBO",
    "ZEELA",
    "HOLTZ",
    "VIOLA",
    "WAVER",
    "RINKA",
    "BOYON",
    "CHOOT",
    "KAGO",
    "SKREE",
    "COVERN",
    "EVIR",
    "TATORI",
    "OUM",
    "PUYO",
    "YARD",
    "ZOA",
    "FUNE",
    "GAMET",
    "GERUTA",
    "SOVA",
    "BULL",
)

def get_hash(fi):
    buf = fi.read()
    rom = FakeROM(buf)

    hash = []

    for x in (0,1,2,3):
        byte = rom.readByte(snes_to_pc(0xdfff00) + x)
        byte = byte & 0x1f
        hash.append(words[byte])

    return " ".join(hash)
