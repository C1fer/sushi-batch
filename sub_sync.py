import os
import subprocess
from datetime import datetime
from halo import Halo
from yaspin import yaspin


# Run sync based on job task
def shift_subs(jobs):
    for job in jobs:
        if job.status != "aPending":
            args = set_args(job)
            exit_code, err_msg = run_shift(args, job)
            # Check if task completed succesfully
            if exit_code == 0:
                job.status = "Completed"
            else:
                job.status = "Failed"
                job.error_message = err_msg  # Store error message


# Set arguments for job execution
def set_args(job):
    args = [
        "sushi",
        "--sample-rate",
        "24000",
        "--src",
        job.src_file,
        "--dst",
        job.dst_file,
    ]

    # Use additional args if found
    if job.task in ("aud-sync-dir", "aud-sync-fil"):
        args.extend(["--script", job.sub_file])

    # Sushi defaults to first audio and sub track if index is not provided
    # Use custom track indexes if specified
    if job.src_aud_track_id is not None:
        args.extend(["--src-audio", job.src_aud_track_id])

    if job.src_sub_track_id is not None:
        args.extend(["--src-script", job.src_sub_track_id])

    return args


# Run Sushi in a subprocess to capture output
def run_shift(args, job):
    # Get log file path
    log_path = set_log_path(job.src_file)

    # Pipe output to stderr to avoid collision with spinner in stdout
    sushi = subprocess.Popen(
        args=args,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Initialize and start spinner
    with yaspin(text=f"Running Job {job.idx}", color="yellow") as sp:
        # Get subprocess output
        _, stderr = sushi.communicate()

        # Write output to file
        with open(log_path, "w") as fil:
            fil.write(stderr)

        # If Sushi exits with error, get error message
        error_message = None
        if sushi.returncode == 0:
            sp.ok("✅")
        else:
            sp.fail("❌")
            lines = stderr.strip().splitlines()
            error_message = "\n".join(lines[1:])
            
    return stderr, error_message


# Set file path to log
def set_log_path(src_file):
    # Set logs directory path
    output_dirpath = os.path.join(os.getcwd(), "Logs")
    os.makedirs(output_dirpath, exist_ok=True)

    # Get job date and time
    current_datetime = datetime.now().strftime("%Y-%m-%d - %H.%M.%S")
    base_name = os.path.basename(src_file.replace(".mkv", ".txt"))

    # Set log file path
    output_filepath = os.path.join(output_dirpath, f"{current_datetime} - {base_name}")

    return output_filepath
