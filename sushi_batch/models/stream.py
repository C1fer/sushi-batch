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
    encode_path: str | None = None
    encode_bitrate: str | None = None

    @property
    def short_display_label(self) -> str:
        return f"ID {self.id}: {self.title} ({self.lang}, {self.channel_layout})" if self.title else f"ID {self.id} ({self.lang}, {self.channel_layout})"

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
