import re

from . import console_utils as cu
from .ffmpeg import FFmpeg


class Stream:
    def __init__(self, idx, lang, info, title=""):
        self.id = idx
        self.lang = lang
        self.info = info
        self.title = title
        self.display_name = f"{idx} - {lang}, {info}" if title == "" else f"{idx} - {title}, {lang}, {info}"

    @classmethod
    def from_tuple(cls, tpl):
        return Stream(*tpl)

    @staticmethod
    def get_streams(file, stream_type):
        """Get available streams from specified file"""
        probe_output = FFmpeg.get_probe_output(file)

        stream_type_pattern = "Audio" if stream_type == "audio" else "Subtitle"

        streams = re.findall(
            r"Stream\s\#0:(\d+)(?:\((.*?)\))?.*?{}:\s*(.*?)\s*?\r?\n"
            r"(?:\s*Metadata:\s*\r?\n"
            r"\s*title\s*:\s*(.*?)\r?\n)?".format(stream_type_pattern),
            probe_output,
            flags=re.VERBOSE,
        )
        return [Stream.from_tuple(x) for x in streams]

    @staticmethod
    def get_stream_lang(streams, stream_id):
        """Get language code of specified stream"""
        for stream in streams:
            if stream.id == stream_id:
                lang = stream.lang if not stream.lang == "" else "und"
                return lang

    @staticmethod
    def get_stream_name(streams, stream_id):
        """Get title/name of specified stream"""
        for stream in streams:
            if stream.id == stream_id:
                return stream.title
            
    @staticmethod
    def has_subtitles(file):
        """Check if specified file has subtitles"""
        return bool(Stream.get_streams(file, "subtitles"))
    
    @staticmethod
    def show_streams(streams):
        """Display available streams for user selection"""
        for stream in streams:
            print(f"{cu.style_reset}{stream.display_name}")
            