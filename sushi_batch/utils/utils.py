import os
import shutil
import subprocess
import sys
from importlib.util import find_spec


def is_app_installed(app_name):
    if is_app_env_var(app_name):
        return True
    
    # If running on Windows, check if executable is inside working directory 
    elif os.name == "nt" and os.path.exists(os.path.join(os.getcwd(), f"{app_name}.exe")): 
        return True
    
    return False


def is_app_env_var(app):
    try:
        subprocess.run(app, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return False
    else:
        return True
    

def clear_logs(dirpath):
    try:
        for entry in os.listdir(dirpath):
            if entry in("Sushi Logs", "Merge Logs", "Aegi-Resample Logs"):
                entry_path = os.path.join(dirpath, entry)
                shutil.rmtree(entry_path)  # Recursively delete the directory
    except OSError as e:
        print(e)


def check_required_packages():
    _PACKAGES = ["art", "colorama", "sushi", "prettytable", "yaspin"]

    for pkg in _PACKAGES:
        if find_spec(pkg) is None:
            print(
                f"\033[91mPackage {pkg} is not installed. Install all dependencies before running the tool\033[00m"
            )
            sys.exit(1)
