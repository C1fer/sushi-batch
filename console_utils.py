import os
from colorama import init, Fore, Style
from time import sleep


init(autoreset=True)
# Store colorama objects to enable direct access from other modules
fore = Fore
style_reset = Style.RESET_ALL


# Clear command line screen
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_error(message):
    print(f"{fore.LIGHTRED_EX}{message}")
    sleep(1)


def print_success(message):
    print(f"\n{fore.LIGHTGREEN_EX}{message}")
    sleep(1)


# Ask for user confirmation
def confirm_action(prompt="Are you sure? (Y/N): "):
    while True:
        confirm = input(f"{fore.CYAN}{prompt}").upper()
        match confirm:
            case "Y":
                return True
            case "N":
                return False
            case others:
                print_error("Wrong input!\n")


# Get option selected by user
def get_choice(options_range, prompt="Select an option: "):
    while True:
        try:
            choice = int(input(f"\n{fore.LIGHTBLACK_EX}{prompt}"))
            if choice in options_range:
                return choice
            else:
                print_error("Invalid choice! Please select a valid option.")
        except ValueError:
            print_error("Invalid choice! Please select a valid option.")


# Look for ffmpeg binary in PATH env var and working directory
def is_ffmpeg_installed():
    # Check if FFmpeg is set on PATH
    if os.environ.get("PATH").find("ffmpeg") != -1:
        return True

    # If FFmpeg is not an env var, look for the binary in working directory
    ffmpeg_bin = ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")  # Set binary name depending on OS
    ffmpeg_path = os.path.join(os.getcwd(), ffmpeg_bin)
    
    if os.path.exists(ffmpeg_path):
        return True

    # If FFmpeg is not found, return false
    return False
