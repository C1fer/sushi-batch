import os
from tkinter import filedialog
from colorama import Fore, Style
import job_queue
import file_formats as ff


# Check if specified file/folder path exists
def check_path_exists(file_list):
    for name in file_list:
        if not os.path.exists(name):
            print(f"{Fore.LIGHTRED_EX}Path {name} does not exist!")
            return False
    return True


# Get folder paths (Directory modes)
def get_paths(gui_enabled):
    
    def get_directory_gui(title):
        return filedialog.askdirectory(title=title)

    def get_directory_cli(prompt):
        return input(prompt).strip('"')

    if gui_enabled:
        src_path = get_directory_gui("Select Source Folder")
        dst_path = get_directory_gui("Select Destination Folder")
    else:
        src_path = get_directory_cli("\nSource Folder Path: ")
        dst_path = get_directory_cli("Destination Folder Path: ")
    
    # Only check if selected path exist  CLI mode
    if not gui_enabled:
        if not check_path_exists([src_path]):
            return None, None

        if not check_path_exists([dst_path]):
            return None, None

    return src_path, dst_path


# Search for files in the specified folders that match the formats
def search_paths(src_path, dst_path, formats, mode):
    src_files = []
    dst_files = []
    sub_files = []

    # Find source files and subtitles
    for root, _, files in os.walk(src_path):
        for name in files:
            if name.endswith(formats):
                src_files.append(os.path.join(root, name))
            if mode == "1" and name.endswith(".ass"):
                sub_files.append(os.path.join(root, name))

    # Find destination files
    for root, _, files in os.walk(dst_path):
        for name in files:
            if name.endswith(formats):
                dst_files.append(os.path.join(root, name))
    
    a = check_files(src_files, dst_files, sub_files, mode)
    # Perform validations on search results
    if check_files(src_files, dst_files, sub_files, mode):
        # Process the jobs on user confirmation
        if job_queue.show_queue(src_files,dst_files, sub_files, mode):
            return src_files, dst_files, sub_files
    
    return None, None, None


# Get files (File-Select modes)
def get_files(mode, gui_enabled):
    src_files = []
    dst_files = []
    sub_files = []

    # Get file paths via file select dialog (GUI Mode)  
    def get_files_gui(title, filetypes):
        return filedialog.askopenfilenames(title=title, filetypes=filetypes)

    # Get file paths via user input (CLI Mode)
    def get_files_cli(prompt):
        file_paths = []
        while True:
            file_path = input(prompt).strip('"')
            file_paths.append(file_path)
            add_another = input("Do you want to add another path? (Y/N): ")
            if add_another.upper() != 'Y': break
        return file_paths

    # Check if GUI mode is enabled
    if gui_enabled:
        if mode == "3":
            src_files = get_files_gui("Select Source Audio Files", ff.audio_filetypes)
            sub_files = get_files_gui("Select Source Subtitle Files", ff.sub_filetypes)
            dst_files = get_files_gui("Select Destination Audio Files", ff.audio_filetypes)

        elif mode == "4":
            src_files = get_files_gui("Select Source Video Files", ff.video_filetypes)
            dst_files = get_files_gui("Select Destination Video Files", ff.video_filetypes)
    else:
        src_files = get_files_cli("\nSource File Path: ")
        dst_files = get_files_cli("\nDestination File Path: ")
        
        if mode == "3":
            sub_files = get_files_cli("\nSubtitle File Path: ")

    # Perform validations on selected files
    if check_files(src_files, dst_files, sub_files, mode, gui_enabled):
        if job_queue.show_queue(src_files, dst_files, sub_files, mode):
            return src_files, dst_files, sub_files
    
    return None, None, None


# Validate found or selected files
def check_files(src_files, dst_files, sub_files, mode, gui_enabled=True):

    # Check if selected files have valid paths (CLI Mode only)
    if (not gui_enabled) and (mode == "3" or mode == "4"):
        if not check_path_exists(src_files):
            return False

        if not check_path_exists(dst_files):
            return False

        if not check_path_exists(sub_files):
            return False

    # Get length of arrays
    src_files_len = len(src_files)
    dst_files_len = len(dst_files)
    sub_files_len = len(sub_files)

    # Check if source files array is empty
    if not src_files_len:
        print(f"{Fore.LIGHTRED_EX}No source files found!")
        return False

    # Check if destination files array is empty
    if not dst_files_len:
        print(f"{Fore.LIGHTRED_EX}No destination files found!")
        return False

    # Check if source and destination files contain the same number of elements
    if src_files_len != dst_files_len:
        print(f"{Fore.LIGHTRED_EX}Number of source files does not match the number of destination files!")
        print(f"({src_files_len} source files, {dst_files_len} destination files){Style.RESET_ALL}")
        return False

    # Check if source and subtitle files contain the same number of elements (audio-based sync)
    if mode == "1"  or mode == "3":
        if src_files_len != sub_files_len:
            print(f"{Fore.LIGHTRED_EX}Number of source files does not match the number of subtitle files!")
            print(f"({src_files_len} source files, {sub_files_len} subtitle files){Style.RESET_ALL}")
            return False

    # If all checks pass, return True
    return True
