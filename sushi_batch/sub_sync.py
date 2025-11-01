import os
import subprocess
from datetime import datetime

from yaspin import yaspin

from . import settings
from .enums import Status, Task
from .subprocess_logger import SubProcessLogger


class Sushi:
    # Set arguments for job execution
    @staticmethod
    def set_args(job):
        args = [
            "sushi",
            "--src",
            job.src_file,
            "--dst",
            job.dst_file,
        ]

        # Use additional args if found
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

    # Calculate average subtitle shift
    @staticmethod
    def calc_avg_shift(output):
        # Keep track of total and count for averaging
        total_shift = 0
        shift_count = 0

        for line in output:
            if "shift:" in line:
                # Split line into parts and get shift value
                parts = line.split()
                shift_val = float(parts[2].removesuffix(","))

                # Add shift value to total and increment count
                total_shift += shift_val
                shift_count += 1
        
        avg_shift = round(total_shift / shift_count, 3)

        return f"{avg_shift:.3f} sec"

    # Run Sushi as a subprocess to capture output
    @staticmethod
    def run(job):
        if settings.config.save_sushi_logs:
            log_path = SubProcessLogger.set_log_path(job.src_file, "Sushi Logs")

        args = Sushi.set_args(job)

        # Pipe output to stderr to avoid collision with spinner in stdout
        sushi = subprocess.Popen(
            args=args,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        with yaspin(text=f"Job {job.idx}", color="cyan", timer=True) as sp:
            # Get subprocess output
            _, stderr = sushi.communicate()

            # Save output to log file only if enabled
            if settings.config.save_sushi_logs:
                SubProcessLogger.save_log_output(log_path, stderr)

            # Split output into list
            lines = stderr.strip().splitlines()

            if sushi.returncode == 0:
                job.status = Status.COMPLETED
                job.result = Sushi.calc_avg_shift(lines)
                sp.ok("✅")
            else:
                job.status = Status.FAILED
                job.result = lines[-1]
                sp.fail("❌")
