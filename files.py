import os
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
def get_directories(gui_enabled):
    # Enter folder paths via command line
    def get_directory_cli(prompt):
        return input(prompt).strip('"')

    # Enter folder paths via folder select dialog
    def get_directory_gui(title):
        return filedialog.askdirectory(title=title)

    if gui_enabled:
        src_path = get_directory_gui("Select Source Folder")
        dst_path = get_directory_gui("Select Destination Folder")
    else:
        src_path = get_directory_cli("\nSource Folder Path: ")
        dst_path = get_directory_cli("Destination Folder Path: ")

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
    if task == "aud-sync-dir":
        formats = ff.audio_formats
    else:
        formats = ff.video_formats

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
        jobs = []
        for src, dst, sub in zip(src_files, dst_files, sub_files):
            new_job = job.Job(src, dst, sub, task)  # Add current task to job
            jobs.append(new_job)
        return jobs
    return None


# Select files
def select_files(gui_enabled, task):
    # Enter file paths via command line
    def select_files_cli(prompt):
        file_paths = []
        while True:
            file_path = input(prompt).strip('"')
            file_paths.append(file_path)
            if not cu.confirm_action("Do you want to add another path? (Y/N): "):
                break
        return file_paths

    # Enter file paths via file select dialog
    def select_files_gui(title, filetypes):
        return filedialog.askopenfilenames(title=title, filetypes=filetypes)

    src_files = []
    dst_files = []
    sub_files = []

    # Open file select dialog if GUI mode is enabled
    if gui_enabled:
        if task == "aud-sync-fil":
            src_files = select_files_gui(
                "Select Source Audio Files", ff.audio_filetypes
            )
            sub_files = select_files_gui(
                "Select Source Subtitle Files", ff.sub_filetypes
            )
            dst_files = select_files_gui(
                "Select Destination Audio Files", ff.audio_filetypes
            )

        elif task == "vid-sync-fil":
            src_files = select_files_gui(
                "Select Source Video Files", ff.video_filetypes
            )
            dst_files = select_files_gui(
                "Select Destination Video Files", ff.video_filetypes
            )
    else:
        src_files = select_files_cli("\nSource File Path: ")
        dst_files = select_files_cli("\nDestination File Path: ")

        if task == "aud-sync-fil":
            sub_files = select_files_cli("\nSubtitle File Path: ")

    src_files_len = len(src_files)

    # Fill subtitle list to avoid passing empty sublist to job queue
    if task == "vid-sync-fil":
        sub_files.extend([None] * src_files_len)

    # Return job list if selected files pass validation
    if check_files(src_files, dst_files, sub_files, task, gui_enabled):
        # Split the elements into job objects if files pass validation
        jobs = []
        for src, dst, sub in zip(src_files, dst_files, sub_files):
            new_job = job.Job(src, dst, sub, task)  # Add current task to job
            jobs.append(new_job)
        return jobs
    return None


# Validate files found on the specified paths or selected by user
def check_files(src_files, dst_files, sub_files, task, gui_enabled=True):
    # Get length of lists
    src_files_len = len(src_files)
    dst_files_len = len(dst_files)
    sub_files_len = len(sub_files)

    # Check if selected files have valid paths (Command line mode only)
    if not gui_enabled and task in ("aud-sync-fil", "vid-sync-fil"):
        if not check_path_exists(src_files):
            return False

        if not check_path_exists(dst_files):
            return False

        if not check_path_exists(sub_files):
            return False

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
        cu.print_error(
            "Number of source files does not match the number of destination files!"
        )
        print(f"({src_files_len} source files, {dst_files_len} destination files)")
        return False

    # Check if source and subtitle files contain the same number of elements (audio sync tasks)
    if task in ("aud-sync-dir", "aud-sync-fil") and src_files_len != sub_files_len:
        cu.print_error(
            "Number of source files does not match the number of subtitle files!"
        )
        print(f"({src_files_len} source files, {sub_files_len} subtitle files)")
        return False

    # If all checks pass, return True
    return True
