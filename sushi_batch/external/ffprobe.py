import json
import subprocess
from pathlib import Path
from typing import Literal, TypedDict

from ..utils import console_utils as cu
from ..utils import utils

StreamCodecType = Literal["audio", "video", "subtitle", "attachment"]

class ProbeTags(TypedDict):
    title: str
    language: str

class ProbeDisposition(TypedDict):
    default: int
    forced: int

class ProbeTrack(TypedDict):
    index: int
    codec_name: str
    codec_type: StreamCodecType
    tags: ProbeTags
    disposition: ProbeDisposition
    width: int | None
    height: int | None
    channel_layout: str | None
    sample_rate: int | None
    bits_per_raw_sample: int | None

class ProbeOutput(TypedDict):
    streams: list[ProbeTrack]

class ParsedProbeOutput(TypedDict):
    audio: list[ProbeTrack]
    video: list[ProbeTrack]
    subtitle: list[ProbeTrack]


class FFprobe:
    is_installed: bool = utils.is_app_installed("ffprobe")
    print_prefix: str = "[FFprobe]"

    @classmethod
    def _get_args(cls, filepath: str) -> list[str]:
        """Construct ffprobe arguments for extracting stream information."""
        return [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json=compact=1",
            "-show_streams",
            "-show_entries",
            "stream=index,codec_name,codec_type,sample_rate,channel_layout,bits_per_raw_sample,width,height:"
            "stream_tags=title,language:"
            "stream_disposition=default,forced",
            filepath,
        ]

    @classmethod
    def _run(cls, filepath: str) -> str:
        """Returns ffprobe output for specified file in JSON format. Used to extract streams information for user selection."""
        if not Path(filepath).is_file():
            raise FileNotFoundError(f"File not found: {filepath}")
    
        process = subprocess.run(
            cls._get_args(filepath),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=True,
        )

        return process.stdout
            
    @classmethod
    def get_parsed_output(cls, filepath: str) -> ParsedProbeOutput:
        """Returns parsed streams extracted from ffprobe output"""
        try:
            streams_by_type: ParsedProbeOutput = {"audio": [], "video": [], "subtitle": []}
    
            media_info: str = cls._run(filepath) 
            if not media_info:
                return streams_by_type

            parsed: ProbeOutput = json.loads(media_info)
            for stream in parsed["streams"]:
                codec_type: StreamCodecType = stream["codec_type"]
                if codec_type != "attachment":
                    streams_by_type[codec_type].append(stream)

            return streams_by_type
        except Exception as e:
            cu.print_error(f"{cls.print_prefix} An error occurred while looking for streams in {filepath}: {e}")
            return streams_by_type
