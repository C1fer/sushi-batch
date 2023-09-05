import os
import subprocess
from datetime import datetime
from yaspin import yaspin
import queue_data as qd


# Run sync based on job task
def shift_subs(jobs, queue):
    for job in jobs:
        if job.status == "Pending":
            args = set_args(job)
            run_shift(args, job)
            
            # Update JSON file afer job execution
            qd.save_list_data(queue)


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

    if job.dst_aud_track_id is not None:
        args.extend(["--dst-audio", job.dst_aud_track_id])

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
        encoding="utf-8",
    )

    # Initialize and start spinner
    with yaspin(text=f"Job {job.idx}", color="cyan", timer=True) as sp:
        # Get subprocess output
        _, stderr = sushi.communicate()

        # Write output to file
        with open(log_path, "w", encoding="utf-8") as fil:
            fil.write(stderr)

        lines = stderr.strip().splitlines()
        
        # Check if task completed succesfully
        if sushi.returncode == 0:
            job.status = "Completed"
            job.result = calc_avg_shift(lines)
            sp.ok("✅")
        else:
            job.status = "Failed"
            job.result = "\n".join(lines[1:])
            sp.fail("❌")


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


# Calculate average sub shift
def calc_avg_shift(output):
    # Keep track of total and count for averaging
    total_shift = 0
    shift_count = 0

    for line in output:
        if "shift:" in line:
            parts = line.split()
        # Extract the numeric part of the shift value (excluding the comma)
            shift_val = parts[2].removesuffix(",")
            # Convert the shift value to an integer and add it to the total
            total_shift += float(shift_val)
            # Increment the shift count
            shift_count += 1

    avg_shift = round(total_shift/shift_count, 3)
    return str(avg_shift) if shift_count > 0 else 0
