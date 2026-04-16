from json import JSONDecoder, JSONEncoder

from ..models.enums import QueueTheme, Status, Task
from ..models.job import Job


class JobEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Job):
            dct = obj.__dict__.copy()
            dct["task"] = obj.task.name
            dct["status"] = obj.status.name
            return dct
        return super().default(obj) 

class JobDecoder(JSONDecoder):
    def __init__(self, **kwargs):
        kwargs.setdefault("object_hook", self.object_hook)
        super().__init__(**kwargs)

    def object_hook(self, dct):
        if "task" in dct:
            dct["task"] = Task[dct["task"]]
        if "status" in dct:
            dct["status"] = Status[dct["status"]]

        return Job(**dct)

class SettingsEncoder(JSONEncoder):
    def default(self, obj):
        from ..models.settings import Settings
        if isinstance(obj, Settings):
            dct = obj.__dict__.copy()
            dct["queue_theme"] = obj.queue_theme.name
            return dct
        return super().default(obj)    

class SettingsDecoder(JSONDecoder):
    def __init__(self, **kwargs):
        kwargs.setdefault("object_hook", self.object_hook)
        super().__init__(**kwargs)

    def object_hook(self, dct):
        if "queue_theme" in dct:
            dct["queue_theme"] = QueueTheme[dct["queue_theme"]]
        
        return dct