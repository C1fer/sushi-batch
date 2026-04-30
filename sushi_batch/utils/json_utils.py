from json import JSONDecoder, JSONEncoder

from ..models.enums import Status, Task 
from ..models.job import Job

class JobEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Job):
            dct = obj.__dict__.copy()
            dct["task"] = obj.task.name
            dct["sync_status"] = obj.sync_status.name
            return dct
        return super().default(obj) 

class JobDecoder(JSONDecoder):
    def __init__(self, **kwargs):
        kwargs.setdefault("object_hook", self.object_hook)
        super().__init__(**kwargs)

    def object_hook(self, dct):
        if "task" in dct:
            dct["task"] = Task[dct["task"]]
        if "sync_status" in dct:
            dct["sync_status"] = Status[dct["sync_status"]]

        return Job(**dct)

