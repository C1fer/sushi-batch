from dataclasses import dataclass

@dataclass
class BaseStream:
    id: int
    codec: str
    lang: str
    title: str
    default: bool
    forced: bool
    display_label: str

@dataclass
class AudioStream(BaseStream):
    channel_layout: str
    selected: bool = False
    encoded: bool = False

@dataclass
class SubtitleStream(BaseStream):
    extension: str
    selected: bool = False

@dataclass
class VideoStream:
    id: int
    width: int
    height: int
    default: bool
