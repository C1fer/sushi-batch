from ..models.stream import SubtitleStream, VideoStream
import subprocess

from ..models import settings as s
from ..utils import utils
from ..utils import console_utils as cu

from .execution_logger import ExecutionLogger

import re
from ..models.job.video_sync_job import VideoSyncJob
from yaspin.core import Yaspin

class SubResampler:
    is_installed: bool = utils.is_app_installed("aegisub-cli")
    whitelisted_resample_extensions: set[str] = {".ass", ".ssa"}
    log_section_name: str = "Subtitle Resample (Aegisub-CLI)"

    @classmethod
    def _try_save_log_content(cls, content: str, log_path: str | None = None, section_name: str | None = None, is_internal: bool = False) -> None:
        if s.config.general["save_merge_logs"] and log_path:
            _section_name = section_name or cls.log_section_name
            ExecutionLogger.save_log_output(log_path, content, section_name= _section_name, is_internal=is_internal)

    
    @staticmethod
    def _get_args(job: VideoSyncJob) -> list[str]:
        selected_stream: SubtitleStream = job.src_streams.get_selected_subtitle_stream()
        return [
            "aegisub-cli",
            f"{job.dst_filepath}.sushi{selected_stream.extension}",
            f"{job.dst_filepath}.sushi_resampled{selected_stream.extension}",
            "tool/resampleres",
            "--video",
            job.dst_filepath,
        ]

    @classmethod
    def run(cls, job: VideoSyncJob, spinner: Yaspin | None = None, log_prefix="[Sub Resampler]") -> bool:
        try: 
            args: list[str] = cls._get_args(job)

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
            cls._try_save_log_content(content=args_log + stdout, log_path=job.merge.log_path, section_name=cls.log_section_name)
               
            if aegisub_resample.returncode == 0:
                job.merge.resample_done = True
                cu.try_print_spinner_message(f"{cu.fore.LIGHTGREEN_EX}{log_prefix} Resampling completed successfully.", spinner)
                return True
            return False
            
        except Exception as e:
            _message: str = f"Error resampling subtitle file: {e}"
            cls._try_save_log_content(content=_message, log_path=job.merge.log_path, section_name=cls.log_section_name)
            cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
            return False
        
    @staticmethod
    def _get_script_resolution(filepath: str) -> tuple[int | None, int | None]:
        """Extracts PlayResX and PlayResY values from the resampled subtitle file"""
        playres_x: int | None = None
        playres_y: int | None = None

        try: 
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "PlayResX" in line:
                        playres_x = int(re.findall(r"\d+", line)[0])
                    elif "PlayResY" in line:
                        playres_y = int(re.findall(r"\d+", line)[0])

                    if playres_x and playres_y:
                        break
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Subtitle file not found: {filepath}") from e
        except Exception as e:
            raise Exception(f"Error getting script resolution: {e}") from e

        return playres_x, playres_y

    @classmethod
    def is_resample_needed(cls, job: VideoSyncJob, spinner: Yaspin | None = None, log_prefix="[Sub Resampler]") -> bool:
        """Determines if subtitle resampling is needed based on script and video resolution"""        
        try:
            selected_stream: SubtitleStream = job.src_streams.get_selected_subtitle_stream()
            if selected_stream.extension not in cls.whitelisted_resample_extensions:
                _message = f"Subtitle format {selected_stream.extension} is not supported for resampling. Skipping resample."
                cls._try_save_log_content(content=_message, log_path=job.merge.log_path, is_internal=True)
                cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
                return False

            
            dst_video_stream: VideoStream = next(stream for stream in job.dst_streams.video if stream.default)
            video_resolution: tuple[int, int] = (dst_video_stream.width, dst_video_stream.height)
            if -1 in video_resolution:
                _message = "Sync target video resolution is unknown. Cannot determine if subtitle resampling is needed."
                cls._try_save_log_content(content=_message, log_path=job.merge.log_path, is_internal=True)
                cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
                return False
            
            script_resolution: tuple[int | None, int | None] = cls._get_script_resolution(f"{job.dst_filepath}.sushi{selected_stream.extension}")
            if None in script_resolution:
                _message = "Script resolution could not be determined from subtitle file. Cannot determine if resampling is needed."
                cls._try_save_log_content(content=_message, log_path=job.merge.log_path, is_internal=True)
                cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
                return False
            
            if video_resolution == script_resolution:
                _message = "Resampling not needed. Script resolution matches video resolution."
                cls._try_save_log_content(content=_message, log_path=job.merge.log_path, is_internal=True)
                cu.try_print_spinner_message(f"{cu.fore.LIGHTBLACK_EX}{log_prefix} {_message}", spinner)
                return False

            cu.try_print_spinner_message(f"{cu.fore.LIGHTYELLOW_EX}{log_prefix} Resampling needed. Script resolution {script_resolution} does not match video resolution {video_resolution}.", spinner)
            return True
        except Exception as e:
            _message = f"An error occurred while determining if subtitle resampling is needed: {e}"
            cls._try_save_log_content(content=_message, log_path=job.merge.log_path, is_internal=True)
            cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
            return False