import sushi.__main__ as sh
from sushi.common import SushiError

# Run sync based on job task
def shift_subs(jobs):
    for job in jobs:
        if job.status == "Pending":
            args = set_args(job)
            try:
                sh.parse_args_and_run(args)
                job.status = "Completed"
            except SushiError as e:
                job.status = "Failed"
                job.error_message = e.args[0]
    

def set_args(job):
    args = []

    if job.task in ("aud-sync-dir", "aud-sync-fil"):
        args = ["--sample-rate", "24000", "--src", job.src_file, "--dst", job.dst_file, "--script", job.sub_file]

    elif job.task in ("vid-sync-dir", "vid-sync-fil"):
        args = ["--sample-rate", "24000", "--src", job.src_file, "--dst", job.dst_file]

        # Sushi defaults to first audio and sub track if index is not provided
        # Use custom track indexes if specified
        if job.src_aud_track_id is not None:
            args.extend(["--src-audio", job.src_aud_track_id])

        if job.src_sub_track_id is not None:
            args.extend(["--src-script", job.src_sub_track_id])

    return args 