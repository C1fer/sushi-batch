import json
from os import path

from ..utils.json_utils import JobEncoder, JobDecoder


class QueuePersistence:
    """Read/write persisted job list JSON for a queue file."""

    def __init__(self, file_path):
        self.file_path = file_path

    def save(self, contents):
        """Write queue contents to the JSON file."""
        with open(self.file_path, "w", encoding="utf-8") as data_file:
            json.dump(contents, data_file, cls=JobEncoder, indent=4)

    def load(self):
        """Load jobs from disk. Returns empty list when the file is missing."""
        if not path.exists(self.file_path):
            return []

        with open(self.file_path, "r", encoding="utf-8") as data_file:
            return json.load(data_file, cls=JobDecoder)
