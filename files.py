import os
import time
from tkinter import filedialog
import job
import file_formats as ff
import console_utils as cu


# Check if specified file or folder path exists
def check_path_exists(file_list):
    for name in file_list:
        if not os.path.exists(name):
            print(f"{cu.fore.LIGHTRED_EX}Path {name} does not exist!")
            return False
    return True


# Get folder paths (Directory modes)
def get_directories():
    # Enter folder paths via folder select dialog
    src_path = filedialog.askdirectory(title="Select Source Folder")
    dst_path = filedialog.askdirectory(title="Select Destination Folder")

    # Validate selected folders
    if not check_path_exists([src_path]):
        return None, None

    if not check_path_exists([dst_path]):
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
    formats = ff.audio_formats if task == "aud-sync-dir" else ff.video_formats

    # Find source files and subtitles
    for root, _, files in os.walk(src_path):
        for name in files:
            if name.endswith(formats):
                src_files.append(os.path.join(root, name))
            if task == "aud-sync-dir" and name.endswith(ff.sub_formats):
                sub_files.append(os.path.join(root, name))

    # Find destination files
    for root, _, files in os.walk(dst_path):
        for name in files:
            if name.endswith(formats):
                dst_files.append(os.path.join(root, name))

    # Fill subtitle list with None values if task is video sync
    if task == "vid-sync-dir":
        sub_files.extend([None] * len(src_files))

    # Perform validations on search results
    if check_files(src_files, dst_files, sub_files, task):
        # Split the elements into job objects if files pass validation
        job_list = create_jobs(zip(src_files, dst_files, sub_files), task)
        return job_list
    return None


# Select files
def select_files(task):
    # Enter file paths via file select dialog
    def select_files_gui(title, filetypes):
        return filedialog.askopenfilenames(title=title, filetypes=filetypes)

    src_files = []
    dst_files = []
    sub_files = []

    # Open file select dialogs based on task
    if task == "aud-sync-fil":
        src_files = select_files_gui("Select Source Audio Files", ff.audio_filetypes)
        sub_files = select_files_gui("Select Source Subtitle Files", ff.sub_filetypes)
        dst_files = select_files_gui("Select Destination Audio Files", ff.audio_filetypes)

    elif task == "vid-sync-fil":
        src_files = select_files_gui("Select Source Video Files", ff.video_filetypes)
        dst_files = select_files_gui("Select Destination Video Files", ff.video_filetypes)

        # Fill subtitle list with None values to avoid passing empty sublist to job queue
        sub_files.extend([None] * len(src_files))

    # Return job list if selected files pass validation
    if check_files(src_files, dst_files, sub_files, task):
        # Split the elements into job objects if files pass validation
        job_list = create_jobs(zip(src_files, dst_files, sub_files), task)
        return job_list
    return None


# Validate files found on the specified paths or selected by user
def check_files(src_files, dst_files, sub_files, task):
    # Get length of lists
    src_files_len = len(src_files)
    dst_files_len = len(dst_files)
    sub_files_len = len(sub_files)

    # Check if there are no source files
    if not src_files_len:
        cu.print_error("No source files found!")
        return False

    # Check if there are no destination files
    if not dst_files_len:
        cu.print_error("No destination files found!")
        return False

    # Check if source and destination files contain the same number of elements
    if src_files_len != dst_files_len:
        print(f"({src_files_len} source files, {dst_files_len} destination files)")
        cu.print_error("Number of source files does not match the number of destination files!")
        return False

    # Check if source and subtitle files contain the same number of elements (audio sync tasks)
    if task in ("aud-sync-dir", "aud-sync-fil") and src_files_len != sub_files_len:
        print(f"({src_files_len} source files, {sub_files_len} subtitle files)")
        cu.print_error("Number of source files does not match the number of subtitle files!")
        return False

    # If all checks pass, return True
    return True


# Create job objects for found and selected files 
def create_jobs(zipped_jobs, task):
    jobs = []
    
    # Create objects and append to list
    for idx, (src, dst, sub) in enumerate(zipped_jobs, start=1):
        new_job = job.Job(idx, src, dst, sub, task)
        jobs.append(new_job)

    return jobs