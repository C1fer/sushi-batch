import subprocess

from yaspin import yaspin

from ..models import settings as s
from ..models.enums import Status
from ..models.job.audio_sync_job import AudioSyncJob
from ..models.job.video_sync_job import VideoSyncJob
from ..utils import console_utils as cu
from ..utils.constants import SushiAdvancedArgKey, SushiAdvancedArgValue
from .execution_logger import ExecutionLogger


class Sushi:
    error_flag = "---SUSHI: CRITICAL ERROR---"
    avg_shift_flag = "Total average shift:"
    warning_flag = "Warning:"
    max_safe_avg_shift = 5  # Defines a threshold for what is considered a "safe" average shift in seconds
    advanced_args_mapping: dict[SushiAdvancedArgKey, tuple[str, SushiAdvancedArgValue]] = {
        "window": ("--window", 10 ),
        "max_window": ("--max-window", 30),
        "rewind_thresh": ("--rewind-thresh", 5),
        "smooth_radius": ("--smooth-radius", 3),
        "max_ts_duration": ("--max-ts-duration", 0.417),
        "max_ts_distance": ("--max-ts-distance", 0.417)
    }

    @classmethod
    def _get_args(cls, job: AudioSyncJob | VideoSyncJob, use_advanced_args: bool = False) -> list[str]:
        base_args: list[str] = [
            "sushi",
            "--src",
            job.src_filepath,
            "--dst",
            job.dst_filepath,
        ]

        track_args: list[str] = [
            "--src-audio", 
            str(job.src_streams.get_selected_audio_stream().id), 
            "--src-script", 
            str(job.src_streams.get_selected_subtitle_stream().id), 
            "--dst-audio", 
            str(job.dst_streams.get_selected_audio_stream().id)
        ] if isinstance(job, VideoSyncJob) else ["--script", job.sub_filepath]
        
        base_args.extend(track_args) 

        if s.config.sync_workflow.get("use_high_quality_resample"):
            base_args.extend(["--sample-rate", "24000"])

        if use_advanced_args:
            cls._add_advanced_args(base_args)

        return base_args
    
    @classmethod
    def _add_advanced_args(cls, args: list[str]) -> None:
        """Add advanced arguments to the base args list if enabled in settings.""" 
        for setting_attr, (arg_name, default_value) in cls.advanced_args_mapping.items():
            current_value: SushiAdvancedArgValue = s.config.sync_workflow["sushi_advanced_args"][setting_attr]
            if current_value is not None and current_value != default_value:
                    args.extend([arg_name, str(current_value)])

    @classmethod
    def _calc_avg_shift(cls, output: list[str]) -> str:
        """Extract average shift from Sushi output."""
        try:
            for line in output[::-1]:  # Iterate in reverse to find the last occurrence
                if line.startswith(cls.avg_shift_flag):
                    shift_str: str = line.split(cls.avg_shift_flag)[1].strip().split()[0]
                    formatted_shift: str = shift_str if shift_str.startswith("-") else f"+{shift_str}" 
                    return formatted_shift
            raise ValueError("Average shift not found")
        except Exception as e:
            return f"Unknown (Error parsing average shift: {str(e)})"

    @classmethod
    def _get_error_message(cls, lines: list[str]) -> str:
        """Extract a useful error message using Sushi critical error flag location."""
        try:
            error_idx: int = lines.index(cls.error_flag)
            if error_idx + 1 < len(lines):
                return lines[error_idx + 1]
            return cls.error_flag
        except ValueError:
            return lines[-1] if lines else "Unknown Sushi error"

    @classmethod
    def run(cls, job: AudioSyncJob | VideoSyncJob, use_advanced_args: bool = False, log_prefix: str = "[Sushi]") -> None:
        file_display = f"{cu.fore.MAGENTA}{job.dst_filepath}{cu.Style.RESET_ALL}"
        title = f"{log_prefix} Syncing subtitles to {file_display}"
        with yaspin(text=title, color="cyan", timer=True, ellipsis="...") as sp:
            try: 
                args: list[str] = cls._get_args(job, use_advanced_args)
                sushi = subprocess.Popen(
                    args=args,
                    stderr=subprocess.PIPE,  # Pipe output to stderr to avoid collision with spinner in stdout
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )

                _, stderr = sushi.communicate()

                if s.config.general["save_sushi_logs"]:
                    log_path: str = ExecutionLogger.set_log_path(job.src_filepath, "Sushi Logs")
                    ExecutionLogger.save_log_output(log_path, stderr)

                lines: list[str] = stderr.strip().splitlines()

                if sushi.returncode != 0:
                    error_msg: str = cls._get_error_message(lines)
                    raise subprocess.SubprocessError(error_msg)

                job.sync.has_warnings = any(cls.warning_flag in line for line in lines)
                job.sync.status = Status.COMPLETED
                job.sync.result = cls._calc_avg_shift(lines)
                sp.ok("✅")
            except Exception as e:
                sp.fail("❌")
                job.sync.status = Status.FAILED
                job.sync.result = str(e)