from enum import Enum


class Formats(Enum):
    AUDIO = (".aac", ".flac", ".m4a", ".opus", ".wav")
    VIDEO = (".avi", ".mp4", ".mkv", ".webm")
    SUBTITLE = (".ass", ".ssa", ".srt")


class FileTypes(Enum):
    AUDIO = [
        (
            "Audio Formats (*.aac, *.flac, *.m4a, *.mp3, *.opus, *.wav)",
            ".aac .flac .m4a .mp3 .opus .wav",
        )
    ]

    VIDEO = [
        (
            "Video formats (*.avi, *.mp4, *.mkv, *.webm)", 
            "avi .mp4 .mkv .webm"
        )
    ]

    SUBTITLE = [
        (
            "Subtitle Formats (*.ass, *.ssa, *.srt )", 
            ".ass .ssa .srt"
        )
    ]


class Task(Enum):
    AUDIO_SYNC_DIR = 1
    AUDIO_SYNC_FIL = 2
    VIDEO_SYNC_DIR = 3
    VIDEO_SYNC_FIL = 4
    JOB_QUEUE = 5


class Status(Enum):
    PENDING = 1
    COMPLETED = 2
    FAILED = 3
    
    
class Section(Enum):
    GEN = "General"
    SRC = "Source File"
    DST = "Destination File"
    SUB = "Synced subtitle"

