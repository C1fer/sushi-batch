from json import JSONDecoder, JSONEncoder

from .enums import Status, Task
from .job import Job


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

        # Return Job instance with modified dict values
        return Job(**dct)
