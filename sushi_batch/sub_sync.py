import subprocess

from yaspin import yaspin

from . import settings
from .enums import Status, Task
from .subprocess_logger import SubProcessLogger


class Sushi:
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
                args.extend(["--src-audio", job.src_aud_id])

            if job.src_sub_id is not None:
                args.extend(["--src-script", job.src_sub_id])

            if job.dst_aud_id is not None:
                args.extend(["--dst-audio", job.dst_aud_id])

        return args

    @staticmethod
    def _calc_avg_shift(output):
        """ Calculate average shift from Sushi output """
        shifts = [
            float(line.split()[2].removesuffix(","))
            for line in output
            if "shift:" in line
        ]
        avg_shift = round(sum(shifts) / len(shifts), 3)

        return f"{avg_shift:.3f} sec"

    @staticmethod
    def run(job):
        args = Sushi._get_args(job)

        sushi = subprocess.Popen(
            args=args,
            stderr=subprocess.PIPE,  # Pipe output to stderr to avoid collision with spinner in stdout
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        with yaspin(text=f"Job {job.idx}", color="cyan", timer=True) as sp:
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
                job.status = Status.FAILED
                job.result = lines[-1]
                sp.fail("❌")
