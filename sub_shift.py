from sushi import __main__ as sh


# Shift timing using audio tracks as reference
def shift_subs_audio(src_files, dst_files, sub_files):
    for idx in range(len(src_files)):
        args = ["--sample-rate", "24000", "--src", src_files[idx], "--dst", dst_files[idx], "--script", sub_files[idx]]
        sh.parse_args_and_run(args)


# Shift timing using videos as reference
def shift_subs_video(src_files, dst_files):
    src_audio_idx, src_sub_idx = None, None

    # Confirm custom track index selection
    choice = input("Do you wish specify the audio and subtitle Track ID for all files? (Y/N): ")

    if choice.upper() == "Y":
        src_audio_idx = input("Source Audio Track ID (will be used for all files): ")  # Set default audio stream index for every file
        src_sub_idx = input("Source Subtitle Track ID (will be used for all files): ")  # Set default subtitle stream index for every file

    for idx in range(len(src_files)):
        args = ["--sample-rate", "12000", "--src", src_files[idx], "--dst", dst_files[idx]]

        # Append track index if specified
        if src_audio_idx is not None:
            args.extend(["--src-audio", src_audio_idx])

        if src_sub_idx is not None:
            args.extend(["--src-script", src_sub_idx])

        sh.parse_args_and_run(args)
