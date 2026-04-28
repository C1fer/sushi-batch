import subprocess
from os import makedirs, path

from yaspin import yaspin

from ..utils import console_utils as cu
from ..utils import utils
from ..models import settings as s

from .subprocess_logger import SubProcessLogger


class MKVMerge:
    is_installed = utils.is_app_installed("mkvmerge")
    
    @classmethod
    def _get_out_filepath(cls, dst_file_path):
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
    
    @classmethod
    def _add_source_file_args(cls, args, job):
        """Add source file specific arguments."""
        args.extend(filter(lambda v: v is not None,
            [
                "--no-audio",
                "--no-video",
                "--no-subtitles",
                "--no-attachments" if not s.config.merge_src_file.get("copy_attachments") else None,
                "--no-chapters" if not s.config.merge_src_file.get("copy_chapters") else None,
                "--no-global-tags" if not s.config.merge_src_file.get("copy_global_tags") else None,
                "--no-track-tags" if not s.config.merge_src_file.get("copy_track_tags") else None,
                job.src_file
            ]
        ))

    @classmethod
    def _add_destination_file_args(cls, args, job, encoded_audio_path=None):
        """Add destination file specific arguments."""
        audio_track_arg = []

        if s.config.merge_dst_file.get("copy_audio_tracks"):
            if encoded_audio_path:
                _track_lang = job.dst_aud_lang if job.dst_aud_lang else "und"
                audio_track_arg = [
                    "--default-track",
                    "0:1",
                    "--language",
                    f"0:{_track_lang}",
                    encoded_audio_path,
                    "--no-audio", # Discard all original audio tracks from dst file since we're adding the encoded track as a new source
                ]
            elif job.dst_aud_id is not None:
                audio_track_arg = ["--audio-tracks", str(job.dst_aud_id)]
        
        args.extend(filter(lambda v: v is not None,
            [
                *audio_track_arg,
                "--no-attachments" if not s.config.merge_dst_file.get("copy_attachments") else None,
                "--no-chapters" if not s.config.merge_dst_file.get("copy_chapters") else None,
                "--no-global-tags" if not s.config.merge_dst_file.get("copy_global_tags") else None,
                "--no-subtitles" if not s.config.merge_dst_file.get("copy_subtitle_tracks") else None,
                "--no-track-tags" if not s.config.merge_dst_file.get("copy_track_tags") else None,
                job.dst_file
            ]
        ))

    @classmethod
    def _add_subtitle_args(cls, args, job, use_resampled_sub):
        """Add subtitle specific arguments."""
        trackname = s.config.merge_synced_sub_file.get("trackname") if s.config.merge_synced_sub_file.get("custom_trackname") else job.src_sub_name
        sub_suffix = f".sushi_resampled{job.src_sub_ext}" if use_resampled_sub else f".sushi{job.src_sub_ext}"
        
        args.extend([
            "--language", f"0:{job.src_sub_lang}",
            "--track-name", f"0:{trackname}",
            "--default-track-flag",
            "0:0" if not s.config.merge_synced_sub_file.get("default_flag") else "0:1",
            "--forced-display-flag",
            "0:0" if not s.config.merge_synced_sub_file.get("forced_flag") else "0:1",
            f"{job.dst_file}{sub_suffix}"
        ])

    @classmethod
    def _get_merge_args(cls, job, use_resampled_sub=False, encoded_audio_path=None):
        output_file = MKVMerge._get_out_filepath(job.dst_file)

        args = [
            "mkvmerge",
            "--output",
            output_file,
        ]

        cls._add_source_file_args(args, job)
        cls._add_destination_file_args(args, job, encoded_audio_path)
        cls._add_subtitle_args(args, job, use_resampled_sub)
        return args

    @classmethod 
    def _show_warnings(cls, output, log_prefix):
        lines = output.splitlines()
        warnings = "\n".join([x.replace("Warning: ", f"{log_prefix} Warning: ") for x in lines if x.startswith("Warning:")])
        if warnings:
            print(f"{cu.fore.LIGHTYELLOW_EX}{warnings}\n")
           
    @classmethod
    def run(cls, job, use_resampled_sub=False, encoded_audio_path=None):
        try:     
            args = cls._get_merge_args(job, use_resampled_sub, encoded_audio_path)
            output_file = path.normpath(args[2])

            log_prefix = f"[Job {job.idx} - MKVMerge]"
            file_display = f"{cu.fore.LIGHTMAGENTA_EX}{output_file}{cu.Style.RESET_ALL}"
            spinner_title = f"{log_prefix} Generating {file_display}"
            with yaspin(text=spinner_title, color="magenta", timer=True) as sp:
                mkv_merge = subprocess.Popen(
                    args=args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

                stdout, _ = mkv_merge.communicate()

                if s.config.general.get("save_mkvmerge_logs"):
                    log_path = SubProcessLogger.set_log_path(output_file, "Merge Logs")
                    SubProcessLogger.save_log_output(log_path, stdout)

                match (mkv_merge.returncode):
                    case 0:
                        sp.ok("✅")
                        job.merged = True
                        job.merged_file = output_file
                        job.merge_has_warnings = False
                    case 1:
                        sp.ok("⚠️")
                        job.merged_file = output_file
                        job.merged = True
                        job.merge_has_warnings = True
                        if not s.config.general.get("save_mkvmerge_logs"):
                            cls._show_warnings(stdout, log_prefix)
                    case 2:
                        lines = stdout.splitlines()
                        error = [x.replace("Error: ", f"{log_prefix} Error: ") for x in lines if x.startswith("Error:")]
                        sp.fail("❌")
                        sp.write(f"{cu.fore.LIGHTRED_EX}{error[0]}\n")
                print()  # Add extra newline after spinner output for readability
        except Exception as e:
                cu.print_error(f"Error generating merged file: {e}")