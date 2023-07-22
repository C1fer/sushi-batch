#To Do: Check sub file handling in directory and single-file video-based sync
import os
import sys
import tkinter as tk
from tkinter import filedialog
from colorama import init, Fore, Style
from sushi import __main__ as sh

init(autoreset=True)  # Set Colorama to reset style after every line
folder_select_gui = True # GUI option toggle

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# Get paths for source and destination files
def get_paths():

    # Use Tkinter folder select dialog if GUI option is enabled
    if folder_select_gui:
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


# Handle job queue
def job_queue(src_files, dst_files, sub_files):

    # Show Job Queue
    clear_screen()
    print(f"{Fore.CYAN}Job Queue")
    
    for idx in range(len(src_files)):
        print(f"\n{Fore.LIGHTBLACK_EX}Job #{idx + 1}")
        print(f"{Fore.LIGHTBLUE_EX}Source file: {src_files[idx]}")
        print(f"{Fore.LIGHTYELLOW_EX}Destination file: {dst_files[idx]}")

        if option == "1" or option == "3":
            print(f"{Fore.LIGHTRED_EX}Subtitle file: {sub_files[idx]}")

    # Confirm queue processing
    choice = input("\nProcess the queue? (Y/N): ")

    if choice.upper() == "Y":
        print(f"{Fore.LIGHTMAGENTA_EX}Processing Queue...\n")
        return True

    return False


# Validate search results
def check_files(src_files_len, dst_files_len, sub_files_len):

    # Check if source or destination folders are empty
    if not src_files_len or not dst_files_len:
        if option == "1":
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
    if option == "1" and src_files_len != sub_files_len:
        print(f"{Fore.LIGHTRED_EX}Number of source files does not match the number of subtitle files!")
        print(f"(Source: {src_files_len} files, Subtitles: {sub_files_len} files){Style.RESET_ALL}")
        return False

    return True


# Search for files that match the specified formats
def find_files(src_path, dst_path, formats):
    src_files = []
    dst_files = []
    sub_files = []

    # Search for tracks and subtitles in the source directory
    for root, _, files in os.walk(src_path):
        for name in files:
            if name.endswith(formats):
                src_files.append(os.path.join(root, name))
            if option == "1" and name.endswith(".ass"):
                sub_files.append(os.path.join(root, name))

    # Search for tracks in the destination directory
    for root, _, files in os.walk(dst_path):
        for name in files:
            if name.endswith(formats):
                dst_files.append(os.path.join(root, name))
    
    # Perform validations on search results
    if check_files(len(src_files), len(dst_files), len(sub_files)):
        # Process the queue if user accepts
        if job_queue(src_files,dst_files, sub_files):
            return src_files, dst_files, sub_files

    return None, None, None


# Shift timing using audio tracks as reference
def shift_subs_audio(src_files, dst_files, sub_files):
    for idx in range(len(src_files)):
        args = ["--sample-rate", "24000", "--src", src_files[idx], "--dst", dst_files[idx], "--script", sub_files[idx]]
        sh.parse_args_and_run(args)


# Shift timing using videos as reference
def shift_subs_mkv(src_files, dst_files):
    src_audio_idx, src_sub_idx = None, None

    # Confirm custom track index selection
    choice = input("Do you wish specify the audio and subtitle Track ID for all files? (Y/N): ")

    if choice.upper() == "Y":
        src_audio_idx = input("Source Audio Track ID (will be used for all files): ")  # Set default audio stream index for every file
        src_sub_idx = input("Source Subtitle Track ID (will be used for all files): ")  # Set default subtitle stream index for every file

    for idx in range(len(src_files)):
        args = ["--sample-rate", "12000", "--src", src_files[idx], "--dst", dst_files[idx]]

        # Append track index if specified
        if src_audio_idx is not None:
            args.extend(["--src-audio", src_audio_idx])

        if src_sub_idx is not None:
            args.extend(["--src-script", src_sub_idx])

        sh.parse_args_and_run(args)


# Validate 
def check_filepaths(src_filepath, dst_filepath, sub_filepath):
    # Validate if files exist
    if not os.path.exists(src_filepath):
        print(f"{Fore.LIGHTRED_EX}Source File {src_filepath} does not exist!")
        return False

    if not os.path.exists(dst_filepath):
        print(f"{Fore.LIGHTRED_EX}Destination File {dst_filepath} does not exist!")
        return False

    if option == "3" and not os.path.exists(sub_filepath):
        print(f"{Fore.LIGHTRED_EX}Subtitle File {sub_filepath} does not exist!")
        return False

    return True


# Get files for single-file modes
def get_filenames():
    sub_filepath = ''

    # Use Tkinter file select dialog if GUI option is enabled
    if folder_select_gui:
        src_filepath = filedialog.askopenfilename(title="Select Source File")
        print(f"Source File Path: {src_filepath}")
        dst_filepath = filedialog.askopenfilename(title="Select Destination File")
        print(f"Destination File Path: {dst_filepath}") 

        # Accept subtitle filepath only on audio single mode
        if option == "3":
            sub_filepath = filedialog.askopenfilename(title="Select Subtitle File")
            print(f"Subtitle File Path: {sub_filepath}") 

    # CLI user input 
    else:
        src_filepath = input("\nSource File Path: ").strip('"')
        dst_filepath = input("Destination File Path: ").strip('"')

        # Accept subtitle filepath only on audio single mode
        if option == "3":
            sub_filepath = input("Subtitle File Path: ").strip('"')

    #if check_filepaths(src_filepath, dst_filepath, sub_filepath):
    # Pass each filepath arg as a list to avoid
    
    if job_queue([src_filepath], [dst_filepath], [sub_filepath]): 
        return src_filepath, dst_filepath, sub_filepath
    return None, None, None
        

def main():
    # Initialize option as a global variable for files validation
    global option 

    while True:
        print(f"""\n{Fore.CYAN}Sushi Batch Tool{Style.RESET_ALL}
        1) Audio-based Sync  (Directory)
        2) Video-based Sync  (Directory) 
        3) Audio-based Sync  (Single-File)
        4) Video-based Sync  (Single-File) 
        5) Exit""")
        option = input("Select an option: ")
        clear_screen()

        if option == "1":
            print(f"{Fore.CYAN}Audio-based Sync (Directory mode)")
            # Get paths and filenames (only execute the shifting if they are valid)
            src_path, dst_path = get_paths()
            if src_path is not None and dst_path is not None:
                src_files, dst_files, sub_files = find_files(src_path, dst_path, tuple(['.aac', '.flac', '.opus']))
                if src_files is not None and dst_files is not None and sub_files is not None:
                    shift_subs_audio(src_files, dst_files, sub_files)

        elif option == "2":
            print(f"{Fore.CYAN}Video-based Sync (Directory mode)")
            # Get paths and filenames (only execute the shifting if they are valid)
            src_path, dst_path = get_paths()
            if src_path is not None and dst_path is not None:
                src_files, dst_files, sub_files = find_files(src_path, dst_path, ".mkv")
                if src_files is not None and dst_files is not None:
                    shift_subs_mkv(src_files, dst_files)

        elif option =="3":
            print(f"{Fore.CYAN}Audio-based Sync (Single-file mode)")
            src_filename, dst_filename, sub_filename = get_filenames()
            if src_filename is not None and dst_filename is not None and sub_filename is not None:
                shift_subs_audio(src_filename, dst_filename, sub_filename)
                
        elif option =="4":
            print(f"{Fore.CYAN}Video-based Sync (Single-file mode)")
            src_filename, dst_filename, _ = get_filenames()
            if src_filename is not None and dst_filename is not None:
                shift_subs_mkv(src_filename, dst_filename)
        else:
            sys.exit()


if __name__ == '__main__':
    main()

 # Test
