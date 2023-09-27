from os import path, makedirs
import subprocess
from yaspin import yaspin
import console_utils as cu
import settings as s
from sub_sync import Sushi


class MKVMerge:
    # Get path for output file
    @staticmethod
    def set_out_filepath(dst_file_path):
        # Split job destination file path for validation
        file_dirname, base_name = path.split(dst_file_path)
        name, ext = path.splitext(base_name)

        # Set output directory path and create directory
        output_dir = path.join(file_dirname, "Merged Files")
        makedirs(output_dir, exist_ok=True)

        # Set output file path
        output_filepath = path.join(output_dir, base_name)
        counter = 1

        # Loop while new file path exists
        while path.exists(output_filepath):
            new_name = f"{name} ({counter}){ext}"
            output_filepath = path.join(output_dir, new_name)
            counter += 1

        return output_filepath

    # Set mkvmerge arguments based on settings
    @staticmethod
    def set_args(job):
        # Set output file path
        output_file = MKVMerge.set_out_filepath(job.dst_file)

        args = [
            "mkvmerge",
            "--output",
            output_file,
            "--no-audio",
            "--no-video",
            "--no-subtitles",
        ]

        # Source file arguments
        if not s.config.src_copy_attachments:
            args.append("--no-attachments")
        if not s.config.src_copy_chapters:
            args.append("--no-chapters")
        if not s.config.src_copy_global_tags:
            args.append("--no-global-tags")
        if not s.config.src_copy_track_tags:
            args.append("--no-track-tags")
        args.append(job.src_file)

        # Destination file arguments
        if not s.config.dst_copy_audio_tracks:
            # Only copy audio track used for synchronization
            args.extend(["--audio-tracks", job.dst_aud_id])
        if not s.config.dst_copy_attachments:
            args.append("--no-attachments")
        if not s.config.dst_copy_chapters:
            args.append("--no-chapters")
        if not s.config.dst_copy_global_tags:
            args.append("--no-global-tags")
        if not s.config.dst_copy_subtitle_tracks:
            args.append("--no-subtitles")
        if not s.config.dst_copy_track_tags:
            args.append("--no-track-tags")
        args.append(job.dst_file)

        # Synced subtitle arguments
        # Use default track name if enabled
        trackname = (
            s.config.sub_trackname
            if s.config.sub_custom_trackname
            else job.src_sub_name
        )
        args.extend(
            [
                "--language",
                f"0: {job.src_sub_lang}",
                "--track-name",
                f"0: {trackname}",
            ]
        )

        if not s.config.sub_default_flag:
            args.extend(["--default-track-flag", "0: 0"])
        if not s.config.sub_forced_flag:
            args.extend(["--forced-display-flag", "0: 0"])
        args.append(f"{job.dst_file}.sushi.ass")

        return args

    # Generate new video file with the specified args
    @staticmethod
    def run(job):
        # Get arguments
        args = MKVMerge.set_args(job)
        output_file = args[2]

        if s.config.save_mkvmerge_logs:
            log_path = Sushi.set_log_path(output_file, "Merge Logs")

        # Run merge with arguments
        mkv_merge = subprocess.Popen(
            args=args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # Initialize spinner
        with yaspin(text=f"{path.basename(output_file)}", color="magenta", timer=True) as sp:
            # Wait for process completion
            stdout, _ = mkv_merge.communicate()

            if s.config.save_mkvmerge_logs:
                with open(log_path, "w", encoding="utf-8") as fil:
                    fil.write(stdout)

            match (mkv_merge.returncode):
                case 0:
                    # Finished successfully
                    sp.ok("✅")
                    job.merged = True
                case 1:
                    # Finished with at least one warning
                    lines = stdout.splitlines()
                    warnings = "\n".join([x for x in lines if x.startswith("Warning:")])
                    sp.ok("⚠️ ")
                    sp.write(f"{cu.fore.LIGHTYELLOW_EX}{warnings}\n")
                    job.merged = True
                case 2:
                    # Finished with error
                    lines = stdout.splitlines()
                    error = [x for x in lines if x.startswith("Error:")]
                    sp.fail("❌")
                    sp.write(f"{cu.fore.LIGHTRED_EX}{error[0]}\n")