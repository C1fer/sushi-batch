import subprocess

from yaspin import yaspin

from ..models import settings
from ..models.enums import Status, Task

from ..utils import console_utils as cu

from .subprocess_logger import SubProcessLogger


class Sushi:
    error_flag = "---SUSHI: CRITICAL ERROR---"
    avg_shift_flag = "Total average shift:"

    @staticmethod
    def _get_args(job):
        args = [
            "sushi",
            "--src",
            job.src_file,
            "--dst",
            job.dst_file,
        ]

        if job.task in (Task.AUDIO_SYNC_DIR, Task.AUDIO_SYNC_FIL):
            args.extend(["--script", job.sub_file])
        else:
            # Sushi defaults to first audio and sub track if index is not provided
            # Use custom track indexes if specified
            if job.src_aud_id is not None:
                args.extend(["--src-audio", str(job.src_aud_id)])

            if job.src_sub_id is not None:
                args.extend(["--src-script", str(job.src_sub_id)])

            if job.dst_aud_id is not None:
                args.extend(["--dst-audio", str(job.dst_aud_id)])

        return args

    @classmethod
    def _calc_avg_shift(cls, output):
        """Extract average shift from Sushi output."""
        try:
            for line in output:
                if line.startswith(cls.avg_shift_flag):
                    shift_str = line.split(cls.avg_shift_flag)[1].strip().split()[0]
                    formatted_shift = shift_str if shift_str.startswith("-") else f"+{shift_str}" 
                    return formatted_shift

        except Exception as e:
            return "Unknown (Couldn't parse shift value: {0})".format(str(e))

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

    @staticmethod
    def run(job):
        file_display = f"{cu.fore.MAGENTA}{job.dst_file}{cu.Style.RESET_ALL}"
        title = f"[Job {job.idx} - Sushi] Syncing subtitles to {file_display}"
        with yaspin(text=title, color="cyan", timer=True) as sp:
            try: 
                args = Sushi._get_args(job)
                sushi = subprocess.Popen(
                    args=args,
                    stderr=subprocess.PIPE,  # Pipe output to stderr to avoid collision with spinner in stdout
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
            
                _, stderr = sushi.communicate()

                if settings.config.save_sushi_logs:
                    log_path = SubProcessLogger.set_log_path(job.src_file, "Sushi Logs")
                    SubProcessLogger.save_log_output(log_path, stderr)

                lines = stderr.strip().splitlines()

                if sushi.returncode == 0:
                    job.status = Status.COMPLETED
                    job.result = Sushi._calc_avg_shift(lines)
                    sp.ok("✅")
                else:
                    error_msg = Sushi._get_error_message(lines)
                    raise subprocess.SubprocessError(error_msg)
            except Exception as e:
                sp.fail("❌")
                job.status = Status.FAILED
                job.result = str(e)
