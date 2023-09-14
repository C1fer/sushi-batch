import subprocess
import re


class Stream:
    def __init__(self, idx, lang, info, title=""):
        self.id = idx
        self.lang = lang
        self.info = info
        self.title = title

    @classmethod
    def from_tuple(cls, tpl):
        return Stream(*tpl)

    @staticmethod
    # Get streams contained in file
    def get_probe_output(filepath):
        process = subprocess.Popen(
            ["ffmpeg", "-hide_banner", "-i", filepath],
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        _, err = process.communicate()
        return err

    @staticmethod
    # Get available streams from file probe output
    def get_streams(file, stream_type):
        # Probe specified file
        probe_output = Stream.get_probe_output(file)

        # Set stream type to filter by
        stream_type_pattern = "Audio" if stream_type == "audio" else "Subtitle"

        streams = re.findall(
            r"Stream\s\#0:(\d+)\((.*?)\).*?{}:\s*(.*?)\s*?\r?\n"
            r"(?:\s*Metadata:\s*\r?\n"
            r"\s*title\s*:\s*(.*?)\r?\n)?".format(stream_type_pattern),
            probe_output,
            flags=re.VERBOSE,
        )
        return [Stream.from_tuple(x) for x in streams]

    @staticmethod
    # Get language code from subtitle stream index
    def get_subtitle_lang(streams, sub_id):
        for stream in streams:
            if stream.id == sub_id:
                return stream.lang

    @staticmethod
    # Get last stream index from a list of streams
    def get_last_id(streams):
        track_id = int(streams[-1].id)
        return track_id

    @staticmethod
    # Show list of available streams
    def show_streams(streams):
        for stream in streams:
            print(f"{stream.id}: {stream.lang}, {stream.title}, {stream.info}")
