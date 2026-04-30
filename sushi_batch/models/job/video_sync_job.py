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

