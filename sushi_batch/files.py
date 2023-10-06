import os

from . import console_utils as cu
from .enums import FileTypes, Formats, Task
from .file_dialogs import FileDialog
from .job import Job
from .streams import Stream


# Get folder paths (Directory modes)
def get_directories():
    # Enter folder paths via folder select dialog
    src_path = FileDialog.askdirectory(title="Select Source Folder")
    dst_path = FileDialog.askdirectory(title="Select Destination Folder")
  
    # Validate selected folders
    if not os.path.exists(src_path):
        cu.print_error(f"Source Path {src_path} does not exist!")
        return None, None

    if not os.path.exists(dst_path):
        cu.print_error(f"Destination Path {dst_path} does not exist!")
        return None, None

    if src_path == dst_path:
        cu.print_error("Source and destination folders are the same!")
        return None, None

    return src_path, dst_path


# Find files in the specified folders that match the formats
def search_directories(src_path, dst_path, task):
    src_files = []
    dst_files = []
    sub_files = []

    # Set formats to filter by based on current task
    formats = (Formats.AUDIO.value if task == Task.AUDIO_SYNC_DIR else Formats.VIDEO.value)

    # Find source files and subtitles
    for root, _, files in os.walk(src_path):
        for name in files:
            if name.endswith(formats):
                src_files.append(os.path.join(root, name))
            if task == Task.AUDIO_SYNC_DIR and name.endswith(Formats.SUBTITLE.value):
                sub_files.append(os.path.join(root, name))

    # Find destination files
    for root, _, files in os.walk(dst_path):
        for name in files:
            if name.endswith(formats):
                dst_files.append(os.path.join(root, name))

    # Fill subtitle list with None values if task is video sync
    if task == Task.VIDEO_SYNC_DIR:
        sub_files.extend([None] * len(src_files))

    # Perform validations on search results
    if validate_files(src_files, dst_files, sub_files, task):
        # Split the elements into job objects if files pass validation
        job_list = create_jobs(src_files, dst_files, sub_files, task)
        return job_list
    return None


# Select files via Tkinter dialog
def select_files(task):
    src_files = []
    dst_files = []
    sub_files = []

    # Enter file paths via file select dialog
    if task == Task.AUDIO_SYNC_FIL:
        src_files = FileDialog.askfilenames("Select Source Audio Files", FileTypes.AUDIO.value)
        sub_files = FileDialog.askfilenames("Select Source Subtitle Files", FileTypes.SUBTITLE.value)
        dst_files = FileDialog.askfilenames("Select Destination Audio Files", FileTypes.AUDIO.value)

    elif task == Task.VIDEO_SYNC_FIL:
        src_files = FileDialog.askfilenames("Select Source Video Files", FileTypes.VIDEO.value)
        dst_files = FileDialog.askfilenames("Select Destination Video Files", FileTypes.VIDEO.value)

        # Fill subtitle list with None values to avoid passing empty sublist to job queue
        sub_files.extend([None] * len(src_files))

    # Return job list if selected files pass validation
    if validate_files(src_files, dst_files, sub_files, task):
        # Split the elements into job objects if files pass validation
        job_list = create_jobs(src_files, dst_files, sub_files, task)
        return job_list
    return None


# Perform validations on selected or found files
def validate_files(src_files, dst_files, sub_files, task):
    # Get lists length
    src_files_len = len(src_files)
    dst_files_len = len(dst_files)
    sub_files_len = len(sub_files)
    # Check if there are no source files
    if not src_files:
        cu.print_error("No source files found!")
        return False

    # Check if there are no destination files
    elif not dst_files:
        cu.print_error("No destination files found!")
        return False

    # Check if source and destination files contain the same number of elements
    elif src_files_len != dst_files_len:
        print(f"({src_files_len} source files, {dst_files_len} destination files)")
        cu.print_error("Number of source files does not match the number of destination files!")
        return False

    # Check if source and subtitle files contain the same number of elements (audio sync tasks)
    elif (
        task in (Task.AUDIO_SYNC_DIR, Task.AUDIO_SYNC_FIL)
        and src_files_len != sub_files_len
    ):
        print(f"({src_files_len} source files, {sub_files_len} subtitle files)")
        cu.print_error( "Number of source files does not match the number of subtitle files!")
        return False

    # If all checks pass, return True
    return True


# Create job objects for found and selected files
def create_jobs(src_files, dst_files, sub_files, task):
    merged_status = False
    
    # Sort sub files if task is not video-sync
    if task not in (Task.VIDEO_SYNC_FIL, Task.VIDEO_SYNC_DIR):
        merged_status = None
        sub_files.sort()
    
    # Generate pairings with sorted lists to avoid incorrect pairings
    zipped_jobs = zip(sorted(src_files), sorted(dst_files), sub_files)
    
    jobs = []
    for idx, (src, dst, sub) in enumerate(zipped_jobs, start=1):
        # Skip pairing if source video does not have at least one subtitle stream
        if task in(Task.VIDEO_SYNC_FIL, Task.VIDEO_SYNC_DIR) and not Stream.has_subtitles(src):
            cu.print_error(f"Source video {src} does not contain subtitles! Skipping...")
            continue
        
        new_job = Job(
            idx=idx, 
            src_file=src, 
            dst_file=dst, 
            sub_file=sub, 
            task=task, 
            merged=merged_status
        )
        jobs.append(new_job)
    return jobs