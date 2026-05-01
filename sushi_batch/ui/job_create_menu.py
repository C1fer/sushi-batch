from typing import Literal, cast

from ..models.enums import Task
from ..models.job.audio_sync_job import AudioSyncJob
from ..models.job.video_sync_job import VideoSyncJob
from ..models.job_queue import JobQueue, JobQueueContents
from ..services.job_creation_service import JobCreationService
from ..utils import console_utils as cu
from ..utils import constants, file_utils
from .queue.temp_queue import show_temp_queue
from .prompts import choice_prompt

FileSelectionMode = Literal["directory", "file-select"]

VIDEO_SYNC_INFO = """Selected tracks are extracted from reference and target videos. Subtitle is adjusted to sync with the target audio.
The generated subtitle can later be merged with the target video in the Job Queue."""

AUDIO_SYNC_INFO = "Provided audio tracks are analyzed to determine timing differences. Subtitle is adjusted to sync with the target audio." 

SYNC_MODES_INFO = """
Directory Mode: Choose source and target folders; matching files are paired automatically by filename.
File-select Mode: Choose source and target files manually."""

MENU_OPTIONS:list[tuple[int, str]] = [
    (1, "Directory Mode"),
    (2, "File-select Mode"),
    (3, "Go Back")
]


def _handle_option_select(task: Task, file_mode: FileSelectionMode) -> bool:
    if file_mode == "directory":
        src, dst = file_utils.get_directories()
        if src and dst:
            src_files, dst_files, sub_files = file_utils.search_directories(src, dst, task)
    else:
        src_files, dst_files, sub_files = file_utils.select_files(task)

    if JobCreationService.validate_files(src_files, dst_files, sub_files, task):
        jobs: list[AudioSyncJob] | list[VideoSyncJob] = (
            JobCreationService.create_audio_sync_jobs(src_files, dst_files, sub_files, task)
            if task in constants.AUDIO_TASKS
            else JobCreationService.create_video_sync_jobs(src_files, dst_files, task)
        )
        temp_queue = JobQueue(contents=cast(JobQueueContents, jobs), in_memory=True)
        should_return_to_home: bool = show_temp_queue(temp_queue, task)
        return should_return_to_home

    return False

def show_job_create_menu(is_video: bool) -> None:
    """Display the job create menu and handle user interactions."""
    header: str = f"Create {'Video' if is_video else 'Audio'} Sync Job"

    while True:
        cu.clear_screen()
        cu.print_header(header)
        cu.print_subheader(VIDEO_SYNC_INFO if is_video else AUDIO_SYNC_INFO)
        print(f"{cu.fore.LIGHTBLACK_EX}{SYNC_MODES_INFO}")

        selected_option: int = choice_prompt.get(
            message="Select an option: ",
            options=MENU_OPTIONS,
            show_frame=True,
            nl_before=True,
        )

        match selected_option:
            case 1:
                task: Task = Task.VIDEO_SYNC_DIR if is_video else Task.AUDIO_SYNC_DIR
                file_mode: FileSelectionMode = "directory"
            case 2:
                task: Task = Task.VIDEO_SYNC_FIL if is_video else Task.AUDIO_SYNC_FIL
                file_mode: FileSelectionMode = "file-select"
            case 3:
                break

        should_return_to_home: bool = _handle_option_select(task, file_mode)
        if should_return_to_home:
            break
