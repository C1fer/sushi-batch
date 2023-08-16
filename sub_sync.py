import sushi.__main__ as sh


# Run sync based on job task
def shift_subs(jobs):
    for job in jobs:
        if job.task in ("aud-sync-dir", "aud-sync-fil"):
            shift_by_audio(job.src_file, job.dst_file, job.sub_file)
        elif job.task in ("vid-sync-dir", "vid-sync-fil"):
            shift_by_video(job.src_file, job.dst_file, job.aud_track_id, job.sub_track_id)
        job.status = "Completed"


# Shift timing using audio tracks as reference
def shift_by_audio(src_file, dst_file, sub_file):
    args = ["--sample-rate", "24000", "--src", src_file, "--dst", dst_file, "--script", sub_file]
    sh.parse_args_and_run(args)


# Shift timing using videos as reference
def shift_by_video(src_file, dst_file, src_audio_id, src_sub_id):
    args = ["--sample-rate", "24000", "--src", src_file, "--dst", dst_file]

    # Sushi defaults to first audio and sub track if index is not provided
    # Use custom track indexes if specified
    if src_audio_id is not None:
        args.extend(["--src-audio", src_audio_id])

    if src_sub_id is not None:
        args.extend(["--src-script", src_sub_id])

    sh.parse_args_and_run(args)
