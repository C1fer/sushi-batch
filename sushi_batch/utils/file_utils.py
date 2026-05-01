import shutil
from pathlib import Path

from ..models.enums import FileTypes, Formats, Status, Task
from ..models.job.audio_sync_job import AudioSyncJob
from ..models.job.video_sync_job import VideoSyncJob
from ..ui.file_dialogs import FileDialog
from . import console_utils as cu


def get_directories() -> tuple[str, str]:
    """Get and validate source and destination directories."""
    src_path: str = FileDialog.askdirectory(title="Select Source Folder")
    dst_path: str = FileDialog.askdirectory(title="Select Destination Folder")

    if src_path == dst_path:
        cu.print_error("Source and destination folders are the same!")
        return "", ""
  
    if not Path(src_path).exists():
        cu.print_error(f"Source Path {src_path} does not exist!")
        return "", ""

    if not Path(dst_path).exists():
        cu.print_error(f"Destination Path {dst_path} does not exist!")
        return "", ""

    return src_path, dst_path


def get_files_in_directory(directory: str, formats: tuple[str, ...]) -> list[str]:
    """Recursively find files matching given formats."""
    matched_files: list[str] = []
    for root, _, files in Path(directory).walk():
        matched_files.extend(
            str(Path(root) / name) 
            for name in files 
            if name.endswith(formats)
        )
    return matched_files


def search_directories(src_path: str, dst_path: str, task: Task) -> tuple[list[str], list[str], list[str]]:
    """Search directories and create jobs from matching files."""
    formats: tuple[str, ...] = Formats.AUDIO.value if task == Task.AUDIO_SYNC_DIR else Formats.VIDEO.value
    
    src_files: list[str] = get_files_in_directory(src_path, formats)
    dst_files: list[str] = get_files_in_directory(dst_path, formats)
    sub_files: list[str] = (
        get_files_in_directory(src_path, Formats.SUBTITLE.value) 
        if task == Task.AUDIO_SYNC_DIR 
        else []
    )

    return src_files, dst_files, sub_files


def select_files(task: Task) -> tuple[list[str], list[str], list[str]]:
    """Select files via dialog and create jobs."""
    src_files: list[str] = []
    dst_files: list[str] = []
    sub_files: list[str] = []

    if task == Task.AUDIO_SYNC_FIL:
        src_files = FileDialog.askfilenames("Select Source Audio Files", FileTypes.AUDIO.value)
        sub_files = FileDialog.askfilenames("Select Source Subtitle Files", FileTypes.SUBTITLE.value)
        dst_files = FileDialog.askfilenames("Select Sync Target Audio Files", FileTypes.AUDIO.value)

    elif task == Task.VIDEO_SYNC_FIL:
        src_files = FileDialog.askfilenames("Select Source Video Files", FileTypes.VIDEO.value)
        dst_files = FileDialog.askfilenames("Select Sync Target Video Files", FileTypes.VIDEO.value)

    return src_files, dst_files, sub_files


def clean_generated_files(job_list: list[AudioSyncJob | VideoSyncJob]) -> None:
    """Delete generated files for the specified jobs"""
    try:
        for job in job_list:
            if job.sync.status is not Status.COMPLETED: 
                continue
            
            suffixes: list[str] = []
            if isinstance(job, AudioSyncJob):
                suffixes.append(f".sushi{Path(job.sub_filepath).suffix}")
            elif isinstance(job, VideoSyncJob):
                sub_ext = job.src_streams.get_selected_subtitle_stream().extension
                suffixes.extend(filter(None, [
                        f".sushi{sub_ext}",
                        f".sushi_resampled{sub_ext}" if job.merge.resample_done else None,
                        f"_encode.{job.merge.audio_encode_codec.lower()}" if job.merge.audio_encode_done and job.merge.audio_encode_codec else None,
                    ]
                ))

            for suffix in suffixes:
                generated_file = Path(f"{job.dst_filepath}{suffix}")
                generated_file.unlink(missing_ok=True)
        cu.print_success("Generated files deleted successfully.")
    except OSError as e:
        cu.print_error(f"Error deleting generated files: {e}")


def clear_logs(dirpath: str) -> None:
    """Clear app logs"""
    try:
        root = Path(dirpath)
        for name in {"Sushi Logs", "Merge Logs", "Aegisub Resample Logs"}: # AegiSub dir left for backwards compatibility
            target: Path = root / name
            if target.exists() and target.is_dir():
                shutil.rmtree(target)
    except OSError as e:
        cu.print_error(f"Error clearing logs: {e}")