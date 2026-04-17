import subprocess

from ..models import settings
from ..utils import utils
from ..utils import console_utils as cu

from .subprocess_logger import SubProcessLogger

import re
class SubResampler:
    is_installed = utils.is_app_installed("aegisub-cli")
    whitelisted_resample_extensions = {".ass", ".ssa"}
    
    @staticmethod
    def _get_args(job):
        return [
            "aegisub-cli",
            f"{job.dst_file}.sushi{job.src_sub_ext}",
            f"{job.dst_file}.sushi_resampled{job.src_sub_ext}",
            "tool/resampleres",
            "--video",
            job.dst_file,
        ]

    @classmethod
    def run(cls, job):
        try: 
            args = cls._get_args(job)

            aegisub_resample = subprocess.Popen(
                args=args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            stdout, _ = aegisub_resample.communicate()

            if settings.config.save_aegisub_resample_logs:
                log_filepath = SubProcessLogger.set_log_path(job.dst_file, "Aegisub Resample Logs")
                SubProcessLogger.save_log_output(log_filepath, stdout)

            return (
                True 
                if aegisub_resample.returncode == 0 
                else False
            )
        except Exception as e:
            cu.print_error(f"Subtitle resampling error: {e}")
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
    def is_resample_needed(cls, job):
        """Determines if subtitle resampling is needed based on script and video resolution"""
        if job.src_sub_ext is None:
            cu.print_error("Source subtitle file extension is unknown. Cannot determine if resampling is needed.")
            return False
        
        if job.src_sub_ext not in cls.whitelisted_resample_extensions:
            cu.print_error(f"Subtitle format {job.src_sub_ext} is not supported for resampling. Skipping resample.")
            return False

        video_resolution = (job.dst_vid_width, job.dst_vid_height)
        if None in video_resolution:
            cu.print_error("Destination video resolution is unknown. Cannot determine if subtitle resampling is needed.")
            return False
        
        script_resolution = cls._get_script_resolution(f"{job.dst_file}.sushi{job.src_sub_ext}")
        if None in script_resolution:
            cu.print_error("Script resolution could not be determined from subtitle file. Cannot determine if resampling is needed.")
            return False
        
        if video_resolution == script_resolution:
            print(f"{cu.fore.LIGHTYELLOW_EX}Subtitle resampling not needed. Script resolution matches video resolution.")
            return False

        return True
