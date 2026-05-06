from dataclasses import dataclass

from ..enums import Task, Status

@dataclass
class JobSync:
    task: Task
    status: Status = Status.PENDING
    has_warnings: bool = False
    result: str | None = None
    log_path: str | None = None

    def to_dct(self) -> dict:
        return {
            "task": self.task.name,
            "status": self.status.name,
            "has_warnings": self.has_warnings,
            "result": self.result,
            "log_path": self.log_path,
        }

    @classmethod
    def from_dct(cls, dct: dict) -> "JobSync":
        return cls(
            task=Task[dct["task"]],
            status=Status[dct["status"]],
            has_warnings=dct["has_warnings"],
            result=dct["result"],
            log_path=dct["log_path"],
        )


@dataclass
class BaseJob:
    def __init__(
        self,
        id: int,
        sync: JobSync,
        src_filepath: str,
        dst_filepath: str,
    ):
        self.id: int = id
        self.sync: JobSync = sync
        self.src_filepath: str = src_filepath
        self.dst_filepath: str = dst_filepath

    def to_dct(self) -> dict:
        return {
            "id": self.id,
            "sync": self.sync.to_dct(),
            "src_filepath": self.src_filepath,
            "dst_filepath": self.dst_filepath,
        }
    
    @classmethod
    def from_dct(cls, dct: dict) -> "BaseJob":
        return cls(
            id=dct["id"],
            sync=JobSync.from_dct(dct["sync"]),
            src_filepath=dct["src_filepath"],
            dst_filepath=dct["dst_filepath"],
        )


