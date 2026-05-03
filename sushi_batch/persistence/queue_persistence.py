from typing import Any
import json
from pathlib import Path
from ..models.job.audio_sync_job import AudioSyncJob
from ..models.job.video_sync_job import VideoSyncJob

class QueuePersistence:
    """Read/write persisted job list JSON for a queue file."""

    def __init__(self, file_path: Path):
        self.file_path: Path = file_path

    def save(self, contents: list[AudioSyncJob | VideoSyncJob]) -> None:
        """Write queue contents to the JSON file."""
        with self.file_path.open("w", encoding="utf-8") as data_file:
            json.dump([job.to_dct() for job in contents], data_file, indent=4)

    def load(self) -> list[dict[str, Any]]:
        """Load jobs from disk.
        Returns an empty list when the file is missing.
        Otherwise, returns a list of to_dct() results from the loaded jobs.
        """
        if not self.file_path.exists():
            return []

        with self.file_path.open("r", encoding="utf-8") as data_file:
            return json.load(data_file)
