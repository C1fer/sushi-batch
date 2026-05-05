from typing import Sequence
import subprocess
from pathlib import Path

from yaspin.core import Yaspin

from ..models import settings as s
from ..models.job.video_sync_job import VideoSyncJob
from ..models.stream import AudioStream, SubtitleStream
from ..utils import console_utils as cu
from ..utils import utils
from .execution_logger import ExecutionLogger


class MKVMerge:
    is_installed: bool = utils.is_app_installed("mkvmerge")
    log_section_name: str = "File Merge (MKVMerge)"

    @classmethod
    def _try_save_log_content(cls, content: str, log_path: str | None = None, section_name: str | None = None, is_internal: bool = False) -> None:
        if s.config.general["save_merge_logs"]:
            _section_name: str = section_name or cls.log_section_name
            ExecutionLogger.save_log_output(log_path, content, section_name =_section_name, is_internal=is_internal)
    
    @classmethod
    def _get_out_filepath(cls, dst_file_path: str) -> str:
        """Generate a unique output file path for the merged MKV file."""
        dst_path: Path = Path(dst_file_path)
        
        output_dir: Path = dst_path.parent / "Merged Files"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_filepath: Path = output_dir / f"{dst_path.stem}{dst_path.suffix}"
        
        counter: int = 1
        while output_filepath.exists():
            output_filepath: Path = output_dir / f"{dst_path.stem} ({counter}){dst_path.suffix}"
            counter += 1

        return str(output_filepath)
    
    @classmethod
    def _add_source_file_args(cls, args: list[str], src_filepath: str) -> None:
        """Add source file specific arguments."""
        args.extend(
            arg for arg in [
                "--no-audio",
                "--no-video",
                "--no-subtitles",
                "--no-attachments" if not s.config.merge_src_file["copy_attachments"] else None,
                "--no-chapters" if not s.config.merge_src_file["copy_chapters"] else None,
                "--no-global-tags" if not s.config.merge_src_file["copy_global_tags"] else None,
                "--no-track-tags" if not s.config.merge_src_file["copy_track_tags"] else None,
                src_filepath
            ] if arg is not None
        )

    @classmethod
    def _get_encoded_audio_track_args(cls, stream: AudioStream, encode_filepath: str) -> list[str]:
        return [
            *(["--default-track", "0:1"] if stream.default else []),
            *(["--forced-display-flag", "0:1"] if stream.forced else []),
            "--track-name", f"0:{stream.title}",
            "--language", f"0:{stream.lang}",
            encode_filepath,
        ]
    
    @classmethod
    def _add_dst_audio_tracks(cls, args: list[str], job: VideoSyncJob) -> None:
        """Add tracks to include in the merged file."""
        if s.config.merge_dst_file["copy_only_selected_sync_audio_track"]:
            sync_target_stream: AudioStream = job.dst_streams.get_selected_audio_stream()
            if sync_target_stream.encoded and sync_target_stream.encode_path:
                args.extend([
                    *cls._get_encoded_audio_track_args(sync_target_stream, sync_target_stream.encode_path),
                    "--no-audio", # Discard all original audio tracks from dst file since we're adding the encoded track as a new source
                ])
            else:
                args.extend(["--audio-tracks", str(sync_target_stream.id)])
        else:
            streams_to_copy: list[str] = []
            for stream in job.dst_streams.audio:
                if stream.encoded and stream.encode_path:
                    args.extend(cls._get_encoded_audio_track_args(stream, stream.encode_path))
                else: 
                    streams_to_copy.append(str(stream.id))
            if streams_to_copy:
                args.extend(["--audio-tracks", ",".join(streams_to_copy)])

    @classmethod
    def _add_destination_file_args(cls, args: list[str], dst_filepath: str) -> None:
        """Add destination file specific arguments."""
        args.extend(
            arg for arg in [
                "--no-attachments" if not s.config.merge_dst_file["copy_attachments"] else None,
                "--no-chapters" if not s.config.merge_dst_file["copy_chapters"] else None,
                "--no-global-tags" if not s.config.merge_dst_file["copy_global_tags"] else None,
                "--no-subtitles" if not s.config.merge_dst_file["copy_subtitle_tracks"] else None,
                "--no-track-tags" if not s.config.merge_dst_file["copy_track_tags"] else None,
                dst_filepath
            ] if arg is not None
        )

    @classmethod
    def _add_subtitle_args(cls, args: list[str], job: VideoSyncJob, use_resampled_sub: bool) -> None:
        """Add subtitle specific arguments."""
        selected_subtitle_stream: SubtitleStream = job.src_streams.get_selected_subtitle_stream()
        trackname: str = (
            s.config.merge_synced_sub_file["trackname"]
            if s.config.merge_synced_sub_file["custom_trackname"]
            else selected_subtitle_stream.title
        )

        sub_suffix: str = (
            f".sushi_resampled{selected_subtitle_stream.extension}"
            if use_resampled_sub
            else f".sushi{selected_subtitle_stream.extension}"
        )

        set_default_flag: bool = (
            selected_subtitle_stream.default
            if not s.config.merge_synced_sub_file["default_flag"]
            else True
        )
        
        set_forced_flag: bool = (
            selected_subtitle_stream.forced
            if not s.config.merge_synced_sub_file["forced_flag"]
            else True
        )

        args.extend([
            "--language", f"0:{selected_subtitle_stream.lang}",
            "--track-name", f"0:{trackname}",
            *(["--default-track-flag", "0:1"] if set_default_flag else []),
            *(["--forced-display-flag", "0:1"] if set_forced_flag else []),
            f"{job.dst_filepath}{sub_suffix}"
        ])

    @classmethod
    def _get_merge_args(cls, job: VideoSyncJob, use_resampled_sub: bool = False) -> list[str]:
        output_file: str = MKVMerge._get_out_filepath(job.dst_filepath)
        args: list[str] = ["mkvmerge", "--output", output_file]

        cls._add_source_file_args(args, job.src_filepath)
        cls._add_dst_audio_tracks(args, job)
        cls._add_destination_file_args(args, job.dst_filepath)
        cls._add_subtitle_args(args, job, use_resampled_sub)
        return args

    @classmethod 
    def _show_warnings(cls, output: str, log_prefix: str, spinner: Yaspin | None = None) -> None:
        lines: list[str] = output.splitlines()
        warnings: str = "\n".join([line.replace("Warning: ", f"{log_prefix} Warning: ") for line in lines if line.startswith("Warning:")])
        if warnings:
            cu.try_print_spinner_message(f"{cu.fore.LIGHTYELLOW_EX}{warnings}\n", spinner)
           
    @classmethod
    def run(
        cls,
        job: VideoSyncJob,
        use_resampled_sub: bool = False,
        spinner: Yaspin | None = None,
        log_prefix="[MKVMerge]",
        log_path: str | None = None,
    ) -> None:
        """Run MKVMerge and handle output logging. log_path can be provided to skip automatic log file creation."""
        try:     
            args: list[str] = cls._get_merge_args(job, use_resampled_sub)
            output_file: str = str(Path(args[2]).resolve())

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

            if log_path:
                args_log: str = f"{ExecutionLogger.internal_log_indicator}Running with arguments: {(' '.join(args))}\n\n"
                cls._try_save_log_content(content=args_log + stdout, log_path=log_path, section_name=cls.log_section_name)

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
                    if not s.config.general["save_merge_logs"]:
                        cls._show_warnings(stdout, log_prefix, spinner)
                case 2:
                    lines: list[str] = stdout.splitlines()
                    error: list[str] = [x.replace("Error: ", f"{log_prefix} Error: ") for x in lines if x.startswith("Error:")]
                    if spinner:
                        spinner.fail("❌")
                        spinner.write(f"{cu.fore.LIGHTRED_EX}{error[0]}\n")
        except Exception as e:
            _message: str = f"Error generating merged file: {e}"
            cls._try_save_log_content(content=_message, log_path=log_path, section_name=cls.log_section_name)
            cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
