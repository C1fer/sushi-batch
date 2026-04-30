import subprocess
from os import makedirs, path

from ..utils import console_utils as cu
from ..utils import utils
from ..models import settings as s

from .execution_logger import ExecutionLogger
from ..models.job.video_sync_job import VideoSyncJob
from yaspin.core import Yaspin


class MKVMerge:
    is_installed = utils.is_app_installed("mkvmerge")
    log_section_name = "File Merge (MKVMerge)"
    
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
    def _add_source_file_args(cls, args, job: VideoSyncJob):
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
                job.src_filepath
            ]
        ))

    @classmethod
    def _add_destination_file_args(cls, args, job: VideoSyncJob, encoded_audio_path: str | None = None):
        """Add destination file specific arguments."""
        audio_track_arg = []
        selected_audio_stream = job.dst_streams.get_selected_audio_stream()
        if s.config.merge_dst_file.get("copy_only_selected_sync_audio_track"):
            if encoded_audio_path:
                _track_lang = selected_audio_stream.lang if selected_audio_stream.lang else "und"
                audio_track_arg = [
                    "--default-track",
                    "0:1",
                    "--language",
                    f"0:{_track_lang}",
                    encoded_audio_path,
                    "--no-audio", # Discard all original audio tracks from dst file since we're adding the encoded track as a new source
                ]
            elif selected_audio_stream.id is not None:
                audio_track_arg = ["--audio-tracks", str(selected_audio_stream.id)]
        
        args.extend(filter(lambda v: v is not None,
            [
                *audio_track_arg,
                "--no-attachments" if not s.config.merge_dst_file.get("copy_attachments") else None,
                "--no-chapters" if not s.config.merge_dst_file.get("copy_chapters") else None,
                "--no-global-tags" if not s.config.merge_dst_file.get("copy_global_tags") else None,
                "--no-subtitles" if not s.config.merge_dst_file.get("copy_subtitle_tracks") else None,
                "--no-track-tags" if not s.config.merge_dst_file.get("copy_track_tags") else None,
                job.dst_filepath
            ]
        ))

    @classmethod
    def _add_subtitle_args(cls, args, job: VideoSyncJob, use_resampled_sub: bool):
        """Add subtitle specific arguments."""
        trackname = s.config.merge_synced_sub_file.get("trackname") if s.config.merge_synced_sub_file.get("custom_trackname") else job.src_streams.get_selected_subtitle_stream().title
        sub_suffix = f".sushi_resampled{job.src_streams.get_selected_subtitle_stream().extension}" if use_resampled_sub else f".sushi{job.src_streams.get_selected_subtitle_stream().extension}"
        
        args.extend([
            "--language", f"0:{job.src_streams.get_selected_subtitle_stream().lang}",
            "--track-name", f"0:{trackname}",
            "--default-track-flag",
            "0:0" if not s.config.merge_synced_sub_file.get("default_flag") else "0:1",
            "--forced-display-flag",
            "0:0" if not s.config.merge_synced_sub_file.get("forced_flag") else "0:1",
            f"{job.dst_filepath}{sub_suffix}"
        ])

    @classmethod
    def _get_merge_args(cls, job: VideoSyncJob, use_resampled_sub: bool = False, encoded_audio_path: str | None = None):
        output_file = MKVMerge._get_out_filepath(job.dst_filepath)

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
    def _show_warnings(cls, output, log_prefix, spinner=None):
        lines = output.splitlines()
        warnings = "\n".join([x.replace("Warning: ", f"{log_prefix} Warning: ") for x in lines if x.startswith("Warning:")])
        if warnings:
            cu.try_print_spinner_message(f"{cu.fore.LIGHTYELLOW_EX}{warnings}\n", spinner)
           
    @classmethod
    def run(cls, job: VideoSyncJob, use_resampled_sub: bool = False, encoded_audio_path: str | None = None, spinner: Yaspin | None = None, log_prefix="[MKVMerge]", log_path: str | None = None) -> None:
        """Run MKVMerge and handle output logging. log_path can be provided to skip automatic log file creation."""
        try:     
            args = cls._get_merge_args(job, use_resampled_sub, encoded_audio_path)
            output_file = path.normpath(args[2])

            file_display = f"{cu.fore.LIGHTMAGENTA_EX}{output_file}{cu.Style.RESET_ALL}"
            spinner_title = f"{log_prefix} Generating {file_display}"
            
            if spinner:
                spinner.text = spinner_title
            else:
                cu.print_warning(spinner_title, nl_before=False, wait=False)

            mkv_merge = subprocess.Popen(
                args=args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            stdout, _ = mkv_merge.communicate()

            if s.config.general.get("save_merge_logs") and log_path:
                args_log = f"{ExecutionLogger.internal_log_indicator}Running with arguments: {(' '.join(args))}\n\n"
                ExecutionLogger.save_log_output(log_path, args_log + stdout, section_name=cls.log_section_name)

            match (mkv_merge.returncode):
                case 0:
                    if spinner:
                        spinner.ok("✅")
                    job.merge.done = True
                    job.merge.merged_filepath = output_file
                    job.merge.has_warnings = False
                case 1:
                    if spinner:
                        spinner.ok("⚠️")
                    job.merge.merged_filepath = output_file
                    job.merge.done = True
                    job.merge.has_warnings = True
                    if not s.config.general.get("save_merge_logs"):
                        cls._show_warnings(stdout, log_prefix, spinner)
                case 2:
                    lines = stdout.splitlines()
                    error = [x.replace("Error: ", f"{log_prefix} Error: ") for x in lines if x.startswith("Error:")]
                    if spinner:
                        spinner.fail("❌")
                        spinner.write(f"{cu.fore.LIGHTRED_EX}{error[0]}\n")
        except Exception as e:
            cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} Error generating merged file: {e}", spinner)