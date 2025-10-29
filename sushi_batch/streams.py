import re
import subprocess

from . import console_utils as cu


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

    # Get streams contained in file
    @staticmethod
    def get_probe_output(filepath):
        process = subprocess.Popen(
            ["ffmpeg", "-hide_banner", "-i", filepath],
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors="ignore"
        )
        _, err = process.communicate()
        return err

    # Get available streams from file probe output
    @staticmethod
    def get_streams(file, stream_type):
        # Probe specified file
        probe_output = Stream.get_probe_output(file)

        # Set stream type to filter by
        stream_type_pattern = "Audio" if stream_type == "audio" else "Subtitle"

        streams = re.findall(
            r"Stream\s\#0:(\d+)(?:\((.*?)\))?.*?{}:\s*(.*?)\s*?\r?\n"
            r"(?:\s*Metadata:\s*\r?\n"
            r"\s*title\s*:\s*(.*?)\r?\n)?".format(stream_type_pattern),
            probe_output,
            flags=re.VERBOSE,
        )
        return [Stream.from_tuple(x) for x in streams]

    # Get language code from subtitle stream index
    @staticmethod
    def get_stream_lang(streams, stream_id):
        for stream in streams:
            if stream.id == stream_id:
                lang = stream.lang if not stream.lang == "" else "und"
                return lang

    # Get trackname code from subtitle stream index
    @staticmethod
    def get_stream_name(streams, stream_id):
        for stream in streams:
            if stream.id == stream_id:
                return stream.title
            
    # Check if specified file has subtitles
    @staticmethod
    def has_subtitles(file):
        if Stream.get_streams(file, "subtitles"):
            return True
        return False
    
    # Show list of available streams
    @staticmethod
    def show_streams(streams):
        for stream in streams:
            print(f"{cu.style_reset}{stream.display_name}")
            