import subprocess
import re
from collections import namedtuple
import console_utils as cu

AudioStreamInfo = namedtuple("AudioStreamInfo", ["id","lang","info",])
SubtitleStreamInfo = namedtuple("SubtitlesStreamInfo", ["id", "lang", "info", "title"])


# Get file media info
def get_file_info(path):
    process = subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-i", path],
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    _, err = process.communicate()
    return err


# Filter audio streams from media info
def get_audio_streams(info):
    streams = re.findall(
        r"Stream\s\#0:(\d+)\((.*?)\).*?Audio:\s*(.*?)\s*?\r?\n",
        info,
        flags=re.VERBOSE,
    )
    return [AudioStreamInfo(int(x[0]), x[1], x[2]) for x in streams]


# Filter subtitle streams from media info
def get_subtitle_streams(info):
    streams = re.findall(
        r"Stream\s\#0:(\d+)\((.*?)\).*?Subtitle:\s*(.*?)\s*?\r?\n"
        r"(?:\s*Metadata:\s*\r?\n"
        r"\s*title\s*:\s*(.*?)\r?\n)?",
        info,
        flags=re.VERBOSE,
    )
    return [SubtitleStreamInfo(int(x[0]), x[1], x[2], x[3]) for x in streams]


# Get streams from file
def get_streams(path, stream_type):
    info = get_file_info(path)
    streams = (
        get_audio_streams(info)
        if stream_type == "audio"
        else get_subtitle_streams(info)
    )

    # Return found streams and indexes for input validation
    return streams, [x.id for x in streams]


# Show specified streams
def show_streams(streams, stream_type):
    if stream_type == "audio":
        print(f"\n{cu.fore.YELLOW}Audio streams")
        for x in streams:
            print(f"{x.id}: {x.lang}, {x.info}")
    else:
        print(f"\n{cu.fore.YELLOW}Subtitle streams")
        for x in streams:
            print(f"{x.id}: {x.lang}, {x.title}, {x.info}")
