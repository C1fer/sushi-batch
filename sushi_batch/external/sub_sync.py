import subprocess

from yaspin import yaspin

from ..models import settings
from ..models.enums import Status

from ..utils import constants
from ..utils import console_utils as cu

from .subprocess_logger import SubProcessLogger


class Sushi:
    error_flag = "---SUSHI: CRITICAL ERROR---"
    avg_shift_flag = "Total average shift:"
    warning_flag = "Warning:"
    max_safe_avg_shift = 5  # Defines a threshold for what is considered a "safe" average shift in seconds
    advanced_args_mapping = {
        "window": ("--window", 10 ),
        "max_window": ("--max-window", 30),
        "rewind_thresh": ("--rewind-thresh", 5),
        "smooth_radius": ("--smooth-radius", 3),
        "max_ts_duration": ("--max-ts-duration", 0.417),
        "max_ts_distance": ("--max-ts-distance", 0.417)
    }

    @classmethod
    def _get_args(cls, job, use_advanced_args=False):
        base_args = [
            "sushi",
            "--src",
            job.src_file,
            "--dst",
            job.dst_file,
        ]

        is_video_task = job.task in constants.VIDEO_TASKS
        track_args = [
            "--src-audio", 
            str(job.src_aud_id), 
            "--src-script", 
            str(job.src_sub_id), 
            "--dst-audio", 
            str(job.dst_aud_id)
        ] if is_video_task else ["--script", job.sub_file]
        base_args.extend(track_args) 

        if settings.config.sync_workflow.get("use_high_quality_resample"):
            base_args.extend(["--sample-rate", "24000"])

        if use_advanced_args:
            cls._add_advanced_args(base_args)

        return base_args
    
    @classmethod
    def _add_advanced_args(cls, args):
        """Add advanced arguments to the base args list if enabled in settings.""" 
        for setting_attr, (arg_name, default_value) in cls.advanced_args_mapping.items():
            current_value = settings.config.sync_workflow.get("sushi_advanced_args", {}).get(setting_attr, None)
            if current_value is not None and current_value != default_value:
                    args.extend([arg_name, str(current_value)])

    @classmethod
    def _calc_avg_shift(cls, output):
        """Extract average shift from Sushi output."""
        try:
            for line in output[::-1]:  # Iterate in reverse to find the last occurrence
                if line.startswith(cls.avg_shift_flag):
                    shift_str = line.split(cls.avg_shift_flag)[1].strip().split()[0]
                    formatted_shift = shift_str if shift_str.startswith("-") else f"+{shift_str}" 
                    return formatted_shift
        except Exception as e:
            return None, "Unknown (Couldn't parse shift value: {0})".format(str(e))

        return None, "Unknown"

    @classmethod
    def _get_error_message(cls, lines):
        """Extract a useful error message using Sushi critical error flag location."""
        try:
            error_idx = lines.index(cls.error_flag)
            if error_idx + 1 < len(lines):
                return lines[error_idx + 1]
            return cls.error_flag
        except ValueError:
            return lines[-1] if lines else "Unknown Sushi error"

    @classmethod
    def run(cls, job, use_advanced_args=False, log_prefix="[Sushi]"):
        file_display = f"{cu.fore.MAGENTA}{job.dst_file}{cu.Style.RESET_ALL}"
        title = f"{log_prefix} Syncing subtitles to {file_display}"
        with yaspin(text=title, color="cyan", timer=True, ellipsis="...") as sp:
            try: 
                args = cls._get_args(job, use_advanced_args)
                sushi = subprocess.Popen(
                    args=args,
                    stderr=subprocess.PIPE,  # Pipe output to stderr to avoid collision with spinner in stdout
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )

                _, stderr = sushi.communicate()

                if settings.config.general.get("save_sushi_logs"):
                    log_path = SubProcessLogger.set_log_path(job.src_file, "Sushi Logs")
                    SubProcessLogger.save_log_output(log_path, stderr)

                lines = stderr.strip().splitlines()

                if sushi.returncode == 0:
                    job.sync_has_warnings = any(cls.warning_flag in line for line in lines)
                    job.sync_status = Status.COMPLETED
                    job.result = cls._calc_avg_shift(lines)
                    sp.ok("✅")
                else:
                    error_msg = cls._get_error_message(lines)
                    raise subprocess.SubprocessError(error_msg)
            except Exception as e:
                sp.fail("❌")
                job.sync_status = Status.FAILED
                job.result = str(e)