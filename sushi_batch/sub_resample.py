import subprocess
from .subprocess_logger import SubProcessLogger
from . import settings
from . import utils

class SubResampler:
    is_installed = utils.is_app_installed("aegisub-cli")
    
    @staticmethod
    def _get_args(job):
        return [
            "aegisub-cli",
            f"{job.dst_file}.sushi.ass",
            f"{job.dst_file}.sushi_resampled.ass",
            "tool/resampleres",
            "--video",
            job.dst_file,
        ]

    @staticmethod
    def run(job):
        args = SubResampler._get_args(job)

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
    