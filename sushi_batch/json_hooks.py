from json import JSONDecoder, JSONEncoder

from .enums import Status, Task
from .job import Job


# Custom JSON encoder for Job class
class JobEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Job):
            # Get copy of object dictionary
            dct = obj.__dict__.copy()
            # Convert Enum instance to Enum name
            dct["task"] = obj.task.name
            dct["status"] = obj.status.name
            return dct
        # Use default behavior for other data types
        return super.default(obj)


# Custom JSON decoder for Job class
class JobDecoder(JSONDecoder):
    def __init__(self, **kwargs):
        kwargs.setdefault("object_hook", self.object_hook)
        super().__init__(**kwargs)

    def object_hook(self, dct):
        # Convert Enum names to Enum instances
        if "task" in dct:
            dct["task"] = Task[dct["task"]]
        if "status" in dct:
            dct["status"] = Status[dct["status"]]

        # Return Job object with modified dict values
        return Job(**dct)
