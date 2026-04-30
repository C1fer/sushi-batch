from dataclasses import dataclass
from pathlib import Path

from .base_job import BaseJob, JobSync

@dataclass
class AudioSyncJob(BaseJob):
    def __init__(
        self,
        id: int,
        sync: JobSync,
        src_filepath: str,
        dst_filepath: str,
        sub_filepath: str = Path().joinpath("sub.srt").as_posix(),
    ):
        self.sub_filepath = str(Path(sub_filepath))
        super().__init__(id, sync, src_filepath, dst_filepath)
