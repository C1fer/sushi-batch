import os
import sys
import argparse
from colorama import init, Fore, Style
import sub_shift
import files


def main():
    init(autoreset=True)  # Set Colorama to reset style after every line

    enable_gui = True
    
    while True:
        print(f"""\n{Fore.CYAN}Sushi Batch Tool{Style.RESET_ALL}
        1) Audio-based Sync  (Directory mode)
        2) Video-based Sync  (Directory mode) 
        3) Audio-based Sync  (File-Select mode)
        4) Video-based Sync  (File-Select mode) 
        5) Exit""")
        mode = input("Select an option: ")
        os.system('cls' if os.name == 'nt' else 'clear') #Clear Screen after mode selection

        match (mode):
            case "1":
                print(f"{Fore.CYAN}Audio-based Sync (Directory mode)")

                # Get paths and filenames (only execute the shifting if they are valid)
                src_path, dst_path = files.get_paths(enable_gui)
                if src_path is not None and dst_path is not None:
                    src_files, dst_files, sub_files = files.search_paths(src_path, dst_path, tuple(['.aac', '.flac', '.opus']), mode)
                    if src_files is not None and dst_files is not None and sub_files is not None:
                        sub_shift.shift_subs_audio(src_files, dst_files, sub_files)
            case "2":
                print(f"{Fore.CYAN}Video-based Sync (Directory mode)")

                # Get paths and filenames (only execute the shifting if they are valid)
                src_path, dst_path = files.get_paths(enable_gui)
                if src_path is not None and dst_path is not None:
                    src_files, dst_files, sub_files = files.search_paths(src_path, dst_path, ".mkv", mode)
                    if src_files is not None and dst_files is not None:
                        sub_shift.shift_subs_video(src_files, dst_files)
            case "3":
                print(f"{Fore.CYAN}Audio-based Sync (Single-file mode)")
                # 
                src_filename, dst_filename, sub_filename = files.get_files(mode, enable_gui)
                if src_filename is not None and dst_filename is not None and sub_filename is not None:
                    sub_shift.shift_subs_audio(src_filename, dst_filename, sub_filename)
            case "4":
                print(f"{Fore.CYAN}Video-based Sync (Single-file mode)")
                # 
                src_filename, dst_filename, _ = files.get_files(mode, enable_gui)
                if src_filename is not None and dst_filename is not None:
                    sub_shift.shift_subs_video(src_filename, dst_filename)
            case others:
                sys.exit()


if __name__ == '__main__':
    main()

 # Test
