import sys
import traceback

from importlib.metadata import version

from .utils import console_utils as cu
from .models import settings as s
from .external.ffmpeg import FFmpeg
from .ui import queue_manager as qm

from .ui.main_menu import run_main_menu

from .utils import utils

utils.check_required_packages()

try: 
    VERSION = version("sushi-batch")
except Exception:
    VERSION = None

def _load_startup_data():
    """Load startup data and allow recovery by resetting the failing state."""
    while True:
        try:
            s.config.handle_load()
        except Exception:
            cu.print_error("An error occurred while loading settings.", False)
            if cu.confirm_action("Restore default settings and restart? (Y/N): "):
                s.config.restore()
                cu.print_success("Settings restored. Initializing...", wait=True)
                break
            raise

        try:
            qm.main_queue.load()
        except Exception:
            cu.print_error("An error occurred while loading the job queue.",False,)
            if cu.confirm_action("Clear queue data and restart? (Y/N): "):
                qm.main_queue.clear(trigger_file_cleanup=False)
                cu.print_success("Queue data cleared. Initializing...", wait=True)
                break
            raise
        return

def main():
    if not FFmpeg.is_installed:
        cu.print_error("FFmpeg could not be found! \nInstall or add the program to PATH before running the tool", False)
        sys.exit(1)

    try:
        _load_startup_data()
    except Exception as e:
        init_trace = traceback.format_exc().rstrip()
        cu.print_error(f"---INIT ERROR---\nStartup initialization failed: {type(e).__name__}: {e}\n{init_trace}", False)
        sys.exit(1)

    run_main_menu(VERSION, s.config)

    
if __name__ == "__main__":
    main()
