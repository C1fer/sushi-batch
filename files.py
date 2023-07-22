import os
from tkinter import filedialog
from colorama import Fore, Style
import job_queue


# Get folder paths for Directory modes
def get_paths(gui_toggle):

    # Use Tkinter folder select dialog if GUI option is enabled
    if gui_toggle:
        src_path = filedialog.askdirectory(title="Select Source Folder")
        print(f"Source Folder Path: {src_path}")
        dst_path = filedialog.askdirectory(title="Select Destination Folder")
        print(f"Destination Folder Path: {dst_path}")
    else:
        src_path = input("\nSource Folder Path: ").strip('"')
        dst_path = input("Destination Folder Path: ").strip('"')
    
    # Check if selected folders exist
    if not os.path.exists(src_path):
        print(f"{Fore.LIGHTRED_EX}Source Path {src_path} does not exist!")
        return None, None
    if not os.path.exists(dst_path):
        print(f"{Fore.LIGHTRED_EX}Destination Path {dst_path} does not exist!")
        return None, None

    return src_path, dst_path


# Search for files that match the specified formats
def search_paths(src_path, dst_path, formats, mode):
    src_files = []
    dst_files = []
    sub_files = []

    # Search for tracks and subtitles in the source directory
    for root, _, files in os.walk(src_path):
        for name in files:
            if name.endswith(formats):
                src_files.append(os.path.join(root, name))
            if mode == "1" and name.endswith(".ass"):
                sub_files.append(os.path.join(root, name))

    # Search for tracks in the destination directory
    for root, _, files in os.walk(dst_path):
        for name in files:
            if name.endswith(formats):
                dst_files.append(os.path.join(root, name))
    
    # Perform validations on search results
    if check_files(len(src_files), len(dst_files), len(sub_files), mode):
        # Process the queue if user accepts
        if job_queue.show_queue(src_files,dst_files, sub_files, mode):
            return src_files, dst_files, sub_files

    return None, None, None


# Get files for File-Select modes
def get_files(mode, gui_toggle):
    src_files = []
    dst_files = []
    sub_files = []

    # Use Tkinter file select dialog if GUI option is enabled
    if gui_toggle:
        src_filepath = filedialog.askopenfilename(title="Select Source File")
        print(f"Source File Path: {src_filepath}")
        dst_filepath = filedialog.askopenfilename(title="Select Destination File")
        print(f"Destination File Path: {dst_filepath}") 

        # Accept subtitle filepath only on audio single mode
        if mode == "3":
            sub_filepath = filedialog.askopenfilename(title="Select Subtitle File")
            print(f"Subtitle File Path: {sub_filepath}") 

    # CLI user input 
    else:
        src_filepath = input("\nSource File Path: ").strip('"')
        dst_filepath = input("Destination File Path: ").strip('"')

        # Accept subtitle filepath only on audio single mode
        if mode == "3":
            sub_filepath = input("Subtitle File Path: ").strip('"')

    #if check_filepaths(src_filepath, dst_filepath, sub_filepath):
    # Pass each filepath arg as a list to avoid
    
    if job_queue.show_queue([src_filepath], [dst_filepath], [sub_filepath], mode): 
        return src_filepath, dst_filepath, sub_filepath
    return None, None, None


# Validate search results
def check_files(src_files_len, dst_files_len, sub_files_len, mode):

    # Check if source or destination folders are empty
    if not src_files_len or not dst_files_len:
        if mode == "1":
            print(f"{Fore.LIGHTRED_EX}No audio files found in source or destination directories.")
        else:
            print(f"{Fore.LIGHTRED_EX}No video files found in source or destination directories.")
        return False

    return True

    # Check if source and destination files contain the same number of elements
    if src_files_len != dst_files_len:
        print(f"{Fore.LIGHTRED_EX}Number of source files does not match the number of destination files!")
        print(f"(Source: {src_files_len} files, Destination: {dst_files_len} files){Style.RESET_ALL}")
        return False

    return True

    # Check if source and subtitle files contain the same number of elements (video-sync only)
    if mode == "1" and src_files_len != sub_files_len:
        print(f"{Fore.LIGHTRED_EX}Number of source files does not match the number of subtitle files!")
        print(f"(Source: {src_files_len} files, Subtitles: {sub_files_len} files){Style.RESET_ALL}")
        return False

    return True


# INCOMPLETE FUNC
def check_filepaths(src_filepath, dst_filepath, sub_filepath):
    # Validate if files exist
    if not os.path.exists(src_filepath):
        print(f"{Fore.LIGHTRED_EX}Source File {src_filepath} does not exist!")
        return False

    if not os.path.exists(dst_filepath):
        print(f"{Fore.LIGHTRED_EX}Destination File {dst_filepath} does not exist!")
        return False

    if mode == "3" and not os.path.exists(sub_filepath):
        print(f"{Fore.LIGHTRED_EX}Subtitle File {sub_filepath} does not exist!")
        return False

    return True
