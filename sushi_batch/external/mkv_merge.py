import subprocess
from os import makedirs, path

from yaspin import yaspin

from ..utils import console_utils as cu
from ..utils import utils
from ..models import settings as s

from .subprocess_logger import SubProcessLogger


class MKVMerge:
    is_installed = utils.is_app_installed("mkvmerge")
    
    @staticmethod
    def _get_out_filepath(dst_file_path):
        """Generate a unique output file path for the merged MKV file."""
        file_dirname, base_name = path.split(dst_file_path)
        name, ext = path.splitext(base_name)

        output_dir = path.join(file_dirname, "Merged Files")
        makedirs(output_dir, exist_ok=True)

        output_filepath = path.join(output_dir, base_name)
        counter = 1

        while path.exists(output_filepath):
            output_filepath = path.join(output_dir, f"{name} ({counter}){ext}")
            counter += 1

        return output_filepath
    
    @staticmethod
    def _add_source_file_args(args, job):
        """Add source file specific arguments."""
        if not s.config.src_copy_attachments:
            args.append("--no-attachments")
        if not s.config.src_copy_chapters:
            args.append("--no-chapters")
        if not s.config.src_copy_global_tags:
            args.append("--no-global-tags")
        if not s.config.src_copy_track_tags:
            args.append("--no-track-tags")
        args.append(job.src_file)

    @staticmethod
    def _add_destination_file_args(args, job):
        """Add destination file specific arguments."""
        if s.config.dst_copy_audio_tracks:
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

    @staticmethod
    def _add_subtitle_args(args, job, use_resampled_sub):
        """Add subtitle specific arguments."""
        trackname = (
            s.config.sub_trackname
            if s.config.sub_custom_trackname
            else job.src_sub_name
        )
        args.extend([
            "--language", f"0: {job.src_sub_lang}",
            "--track-name", f"0: {trackname}",
        ])

        if not s.config.sub_default_flag:
            args.extend(["--default-track-flag", "0: 0"])
        if not s.config.sub_forced_flag:
            args.extend(["--forced-display-flag", "0: 0"])

        sub_suffix = ".sushi_resampled.ass" if use_resampled_sub else ".sushi.ass"
        args.append(f"{job.dst_file}{sub_suffix}")

    @staticmethod
    def _get_merge_args(job, use_resampled_sub=False):
        output_file = MKVMerge._get_out_filepath(job.dst_file)

        args = [
            "mkvmerge",
            "--output",
            output_file,
            "--no-audio",
            "--no-video",
            "--no-subtitles",
        ]

        MKVMerge._add_source_file_args(args, job)
        MKVMerge._add_destination_file_args(args, job)
        MKVMerge._add_subtitle_args(args, job, use_resampled_sub)

        return args

    @staticmethod
    def run(job, use_resampled_sub=False):
        with yaspin(text=f"{path.basename(output_file)}", color="magenta", timer=True) as sp:
            try:     
                args = MKVMerge._get_merge_args(job, use_resampled_sub)
                output_file = args[2]
                
                mkv_merge = subprocess.Popen(
                    args=args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

                stdout, _ = mkv_merge.communicate()

                if s.config.save_mkvmerge_logs:
                    log_path = SubProcessLogger.set_log_path(output_file, "Merge Logs")
                    SubProcessLogger.save_log_output(log_path, stdout)

                match (mkv_merge.returncode):
                    case 0:
                        sp.ok("✅")
                        job.merged = True
                    case 1:
                        lines = stdout.splitlines()
                        warnings = "\n".join([x for x in lines if x.startswith("Warning:")])
                        sp.ok("⚠️ ")
                        sp.write(f"{cu.fore.LIGHTYELLOW_EX}{warnings}\n")
                        job.merged = True
                    case 2:
                        lines = stdout.splitlines()
                        error = [x for x in lines if x.startswith("Error:")]
                        sp.fail("❌")
                        sp.write(f"{cu.fore.LIGHTRED_EX}{error[0]}\n")
            except Exception as e:
                cu.print_error(f"Merge error: {e}")