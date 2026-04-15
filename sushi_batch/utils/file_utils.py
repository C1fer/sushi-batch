from os import path, walk

from ..models.enums import FileTypes, Formats, Task
from ..models.job import Job
from ..models.streams import Stream


from . import console_utils as cu
from .file_dialogs import FileDialog



def get_directories():
    """Get and validate source and destination directories."""
    src_path = FileDialog.askdirectory(title="Select Source Folder")
    dst_path = FileDialog.askdirectory(title="Select Destination Folder")

    if src_path == dst_path:
        cu.print_error("Source and destination folders are the same!")
        return None, None
  
    if not path.exists(src_path):
        cu.print_error(f"Source Path {src_path} does not exist!")
        return None, None

    if not path.exists(dst_path):
        cu.print_error(f"Destination Path {dst_path} does not exist!")
        return None, None

    return src_path, dst_path


def get_files_in_directory(directory, formats, task):
    """Recursively find files matching given formats."""
    matched_files = []
    for root, _, files in walk(directory):
        matched_files.extend(
            path.join(root, name) 
            for name in files 
            if name.endswith(formats)
        )
    return matched_files


def search_directories(src_path, dst_path, task):
    """Search directories and create jobs from matching files."""
    formats = Formats.AUDIO.value if task == Task.AUDIO_SYNC_DIR else Formats.VIDEO.value
    
    src_files = get_files_in_directory(src_path, formats, task)
    dst_files = get_files_in_directory(dst_path, formats, task)
    sub_files = (
        get_files_in_directory(src_path, Formats.SUBTITLE.value, task) 
        if task == Task.AUDIO_SYNC_DIR 
        else []
    )

    if validate_files(src_files, dst_files, sub_files, task):
        return create_jobs(src_files, dst_files, sub_files, task)
    return None


def select_files(task):
    """Select files via dialog and create jobs."""
    src_files = dst_files = sub_files = []

    if task == Task.AUDIO_SYNC_FIL:
        src_files = FileDialog.askfilenames("Select Source Audio Files", FileTypes.AUDIO.value)
        sub_files = FileDialog.askfilenames("Select Source Subtitle Files", FileTypes.SUBTITLE.value)
        dst_files = FileDialog.askfilenames("Select Destination Audio Files", FileTypes.AUDIO.value)

    elif task == Task.VIDEO_SYNC_FIL:
        src_files = FileDialog.askfilenames("Select Source Video Files", FileTypes.VIDEO.value)
        dst_files = FileDialog.askfilenames("Select Destination Video Files", FileTypes.VIDEO.value)

    if validate_files(src_files, dst_files, sub_files, task):
        return create_jobs(src_files, dst_files, sub_files, task)
    return None


def validate_files(src_files, dst_files, sub_files, task):
    """Validate file counts and task requirements."""
    src_len, dst_len, sub_len = len(src_files), len(dst_files), len(sub_files)

    validations = [
        (src_len == 0, "No source files found!"),
        (dst_len == 0, "No destination files found!"),
        (src_len != dst_len, f"Source ({src_len}) and destination ({dst_len}) file counts don't match!"),
        (task in (Task.AUDIO_SYNC_DIR, Task.AUDIO_SYNC_FIL) and src_len != sub_len, 
         f"Audio ({src_len}) and subtitle ({sub_len}) file counts don't match!"),
    ]

    for condition, error_msg in validations:
        if condition:
            cu.print_error(error_msg)
            return False
    return True


def create_jobs(src_files, dst_files, sub_files, task):
    """Create job objects from files."""
    is_video_task = task in (Task.VIDEO_SYNC_FIL, Task.VIDEO_SYNC_DIR)
    
    subtitles = sorted(sub_files) if not is_video_task else [None] * len(src_files)

    # Generate pairings with sorted lists to avoid incorrect pairings
    zipped_jobs = zip(sorted(src_files), sorted(dst_files), subtitles)
    
    jobs = []
    for idx, (src, dst, sub) in enumerate(zipped_jobs, start=1):
        if is_video_task and not Stream.has_subtitles(src):
            cu.print_error(f"Source video {src} does not contain subtitles! Skipping...")
            continue

        jobs.append(
            Job(
                idx=idx,
                src_file=src,
                dst_file=dst,
                sub_file=sub,
                task=task,
                merged= False if is_video_task else None
            )
        )
    return jobs