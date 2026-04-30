import subprocess

from ..models import settings
from ..utils import utils
from ..utils import console_utils as cu

from .execution_logger import ExecutionLogger

import re
from ..models.job.video_sync_job import VideoSyncJob
from yaspin.core import Yaspin

class SubResampler:
    is_installed = utils.is_app_installed("aegisub-cli")
    whitelisted_resample_extensions = {".ass", ".ssa"}
    log_section_name = "Subtitle Resample (Aegisub-CLI)"

    @classmethod
    def _try_save_log_content(cls, log_path, content, section_name = None, is_internal=False):
        if settings.config.general.get("save_merge_logs") and log_path:
            _section_name = section_name or cls.log_section_name
            ExecutionLogger.save_log_output(log_path, content, section_name= _section_name, is_internal=is_internal)

    
    @staticmethod
    def _get_args(job: VideoSyncJob) -> list[str]:
        selected_stream = job.src_streams.get_selected_subtitle_stream()
        return [
            "aegisub-cli",
            f"{job.dst_filepath}.sushi{selected_stream.extension}",
            f"{job.dst_filepath}.sushi_resampled{selected_stream.extension}",
            "tool/resampleres",
            "--video",
            job.dst_filepath,
        ]

    @classmethod
    def run(cls, job: VideoSyncJob, spinner: Yaspin | None = None, log_prefix="[Sub Resampler]", log_path: str | None = None) -> bool:
        try: 
            args = cls._get_args(job)

            if spinner:
                spinner.text = f"{log_prefix} Resampling subtitle file"
            else:
                cu.print_warning(f"{log_prefix} Resampling subtitle file", nl_before=False, wait=False)

            aegisub_resample = subprocess.Popen(
                args=args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            args_log = f"{ExecutionLogger.internal_log_indicator}Running with arguments: {(' '.join(args))}\n\n"

            stdout, _ = aegisub_resample.communicate()

            cls._try_save_log_content(log_path, args_log + stdout)

            if aegisub_resample.returncode == 0:
                job.merge.resample_done = True
                cu.try_print_spinner_message(f"{cu.fore.LIGHTGREEN_EX}{log_prefix} Resampling completed successfully.", spinner)
                return True
            return False
            
        except Exception as e:
            cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} Subtitle resampling error: {e}", spinner)
            return False
        
    @staticmethod
    def _get_script_resolution(filepath):
        """Extracts PlayResX and PlayResY values from the resampled subtitle file"""
        playres_x = None
        playres_y = None

        try: 
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "PlayResX" in line:
                        playres_x = int(re.findall(r"\d+", line)[0])
                    elif "PlayResY" in line:
                        playres_y = int(re.findall(r"\d+", line)[0])

                    if playres_x and playres_y:
                        break
        except Exception:
            return None, None

        return playres_x, playres_y

  
    @classmethod
    def is_resample_needed(cls, job: VideoSyncJob, spinner: Yaspin | None = None, log_prefix="[Sub Resampler]", log_path: str | None = None) -> bool:
        """Determines if subtitle resampling is needed based on script and video resolution"""        
        try:
            selected_stream = job.src_streams.get_selected_subtitle_stream()
            if selected_stream.extension not in cls.whitelisted_resample_extensions:
                _message = f"Subtitle format {selected_stream.extension} is not supported for resampling. Skipping resample."
                cls._try_save_log_content(log_path, _message, is_internal=True)
                cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
                return False

            
            dst_video_stream = next(stream for stream in job.dst_streams.video if stream.default)
            video_resolution = (dst_video_stream.width, dst_video_stream.height)
            if None in video_resolution:
                _message = "Sync target video resolution is unknown. Cannot determine if subtitle resampling is needed."
                cls._try_save_log_content(log_path, _message, is_internal=True)
                cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
                return False
            
            script_resolution = cls._get_script_resolution(f"{job.dst_filepath}.sushi{selected_stream.extension}")
            if None in script_resolution:
                _message = "Script resolution could not be determined from subtitle file. Cannot determine if resampling is needed."
                cls._try_save_log_content(log_path, _message, is_internal=True)
                cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
                return False
            
            if video_resolution == script_resolution:
                _message = "Resampling not needed. Script resolution matches video resolution."
                cls._try_save_log_content(log_path, _message, is_internal=True)
                cu.try_print_spinner_message(f"{cu.fore.LIGHTBLACK_EX}{log_prefix} {_message}", spinner)
                return False

            cu.try_print_spinner_message(f"{cu.fore.LIGHTYELLOW_EX}{log_prefix} Resampling needed. Script resolution {script_resolution} does not match video resolution {video_resolution}.", spinner)
            return True
        except Exception as e:
            _message = f"An error occurred while determining if subtitle resampling is needed: {e}"
            cls._try_save_log_content(log_path, _message, is_internal=True)
            cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
            return False