from tortoise.models import Model
from tortoise import fields
from enum import IntEnum


class RaceStatus(IntEnum):
    WAITING = 0
    ROOM_SCHEDULED = 10
    ROOM_OPENED = 20
    SEED_ROLLED = 30
    RACE_STARTED = 40


class Race(Model):
    id = fields.IntField(pk=True)
    start_time = fields.DatetimeField()
    description = fields.TextField()
    baseurl = fields.TextField(
        default='https://randommetroidsolver.pythonanywhere.com')
    team = fields.BooleanField(default=False)
    skills_preset = fields.TextField(null=True)
    settings_preset = fields.TextField(null=True)
    custom_settings = fields.JSONField(default={})

    status = fields.SmallIntField(default=RaceStatus.WAITING)
    url = fields.TextField(null=True)

    class Meta:
        table = "race"

    def __str__(self):
        return self.description

    def update_from_yaml(self, yrace):
        self.description = yrace.get('desc')
        self.baseurl = yrace.get('baseurl')
        self.skills_preset = yrace.get('skills_preset')
        self.settings_preset = yrace.get('settings_preset')
        self.custom_settings = yrace.get('custom_settings')
        self.team = yrace.get('team', False)

    @classmethod
    def from_yaml(cls, yrace):
        r = Race()
        r.start_time = yrace.get('datetime')
        r.update_from_yaml(yrace)
        return r
