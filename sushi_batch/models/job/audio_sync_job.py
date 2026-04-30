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

    def to_dct(self) -> dict:
        dct = super().to_dct()
        dct.update({
            "sub_filepath": self.sub_filepath,
        })
        return dct
    
    @classmethod
    def from_dct(cls, dct: dict) -> "AudioSyncJob":
        return cls(
            id=dct["id"],
            sync=JobSync.from_dct(dct["sync"]),
            src_filepath=dct["src_filepath"],
            dst_filepath=dct["dst_filepath"],
            sub_filepath=dct["sub_filepath"],
        )
