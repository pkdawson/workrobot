from zoneinfo import ZoneInfo
from datetime import datetime

RACETZ = ZoneInfo("America/New_York")


def to_datetime(tstr):
    # parse string as Eastern time, then convert to local system time
    return (
        datetime.fromisoformat(tstr)
        .replace(tzinfo=RACETZ)
        .astimezone()
        .replace(tzinfo=None)
    )


# __all__ = ['RACETZ']
