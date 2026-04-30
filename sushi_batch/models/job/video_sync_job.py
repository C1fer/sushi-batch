from typing import Literal
from dataclasses import dataclass

from .base_job import BaseJob, JobSync
from ..stream import VideoStream, AudioStream, SubtitleStream


@dataclass
class JobMerge:
    done: bool = False
    merged_filepath: str | None = None
    has_warnings: bool = False
    resample_done: bool = False
    audio_encode_done: bool = False
    audio_encode_codec: str | None = None
    audio_encode_encoder: str | None = None
    audio_encode_bitrate: str | None = None


@dataclass
class JobSub:
    filepath: str 


@dataclass
class JobMediaStreams:
    video: list[VideoStream]
    audio: list[AudioStream]
    subtitle: list[SubtitleStream]

    def to_dct(self) -> dict:
        return {
            "video": [stream.__dict__ for stream in self.video],
            "audio": [stream.__dict__ for stream in self.audio],
            "subtitle": [stream.__dict__ for stream in self.subtitle]
        }
        
    
    @classmethod
    def from_dct(cls, dct: dict) -> "JobMediaStreams":
        return cls(
            video=[VideoStream(**stream) for stream in dct["video"]],
            audio=[AudioStream(**stream) for stream in dct["audio"]],
            subtitle=[SubtitleStream(**stream) for stream in dct["subtitle"]]
        )
    
    def get_selected_audio_stream(self) -> AudioStream:
        return next(stream for stream in self.audio if stream.default)
    
    def get_selected_subtitle_stream(self) -> SubtitleStream:
        return next(stream for stream in self.subtitle if stream.default)

    def set_selected_audio_stream_by_id(self, stream_id: int) -> None:
        stream = next(stream for stream in self.audio if stream.id == stream_id)
        if stream:
            stream.selected = True
        else:
            raise ValueError(f"Stream with ID {stream_id} not found")

    def set_selected_subtitle_stream_by_id(self, stream_id: int) -> None:
        stream = next(stream for stream in self.subtitle if stream.id == stream_id)
        if stream:
            stream.selected = True
        else:
            raise ValueError(f"Stream with ID {stream_id} not found")


class VideoSyncJob(BaseJob):
    def __init__(
        self,
        id: int,
        src_filepath: str,
        dst_filepath: str,
        sync: JobSync,
        src_streams: JobMediaStreams,
        dst_streams: JobMediaStreams,
        merge: JobMerge = JobMerge()
    ):
        self.src_streams = src_streams
        self.dst_streams = dst_streams
        self.merge = merge
        super().__init__(id, sync, src_filepath, dst_filepath)

    def to_dct(self) -> dict:
        dct = super().to_dct()
        dct.update({
            "src_streams": self.src_streams.to_dct(),
            "dst_streams": self.dst_streams.to_dct(),
            "merge": self.merge.__dict__
        })
        return dct
    
    @classmethod
    def from_dct(cls, dct: dict) -> "VideoSyncJob":
        return cls(
            id=dct["id"],
            sync=JobSync.from_dct(dct["sync"]),
            src_filepath=dct["src_filepath"],
            dst_filepath=dct["dst_filepath"],
            src_streams=JobMediaStreams.from_dct(dct["src_streams"]),
            dst_streams=JobMediaStreams.from_dct(dct["dst_streams"]),
            merge=JobMerge(**dct["merge"])
        )