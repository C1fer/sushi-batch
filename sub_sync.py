import os
import subprocess
from datetime import datetime
from yaspin import yaspin
from enums import Task, Status
import settings as s

class Sushi:
    # Set arguments for job execution
    @staticmethod
    def set_args(job):
        # Set sample rate for search algorithm
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

    # Set log file path
    @staticmethod
    def set_log_path(src_file, dir_name):
        # Get job execution date and time
        current_datetime = datetime.now().strftime("%Y-%m-%d - %H.%M.%S")

        # Set logs directory path
        output_dirpath = os.path.join(s.config.data_path, dir_name)
        os.makedirs(output_dirpath, exist_ok=True)

        # Get source file name and extension
        base_name = os.path.basename(src_file)
        name, ext = os.path.splitext(base_name)

        # Set log file path
        output_filepath = os.path.join(output_dirpath, f"{current_datetime} - {name}.log")

        return output_filepath

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
        
        # Get average shift 
        avg_shift = round(total_shift / shift_count, 3)

        # Return average shift with three decimal places regardless of value
        return f"{avg_shift:.3f} sec"

    # Run Sushi as a subprocess to capture output
    @staticmethod
    def run(job):
        # Get log file path only if enabled
        if s.config.save_sushi_logs:
            log_path = Sushi.set_log_path(job.src_file, "Sushi Logs")

        # Get sushi arguments
        args = Sushi.set_args(job)

        # Pipe output to stderr to avoid collision with spinner in stdout
        sushi = subprocess.Popen(
            args=args,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Initialize and start spinner
        with yaspin(text=f"Job {job.idx}", color="cyan", timer=True) as sp:
            # Get subprocess output
            _, stderr = sushi.communicate()

            # Save output to log file only if enabled
            if s.config.save_sushi_logs:
                with open(log_path, "w") as fil:
                    fil.write(stderr)

            # Split output into list
            lines = stderr.strip().splitlines()

            # Check if task completed succesfully
            if sushi.returncode == 0:
                job.status = Status.COMPLETED
                job.result = Sushi.calc_avg_shift(lines)
                sp.ok("✅")
            else:
                job.status = Status.FAILED
                job.result = lines[-1]
                sp.fail("❌")
