import json
from os import path
from ..models.job.audio_sync_job import AudioSyncJob
from ..models.job.video_sync_job import VideoSyncJob

class QueuePersistence:
    """Read/write persisted job list JSON for a queue file."""

    def __init__(self, file_path):
        self.file_path = file_path

    def save(self, contents: list[AudioSyncJob | VideoSyncJob]) -> None:
        """Write queue contents to the JSON file."""
        with open(self.file_path, "w", encoding="utf-8") as data_file:
            json.dump([job.to_dct() for job in contents], data_file, indent=4)

    def load(self) :
        """Load jobs from disk. Returns empty list when the file is missing."""
        if not path.exists(self.file_path):
            return []

        with open(self.file_path, "r", encoding="utf-8") as data_file:
            return json.load(data_file)
