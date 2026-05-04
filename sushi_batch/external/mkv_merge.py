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
    def _add_source_file_args(cls, args, job: VideoSyncJob) -> None:
        """Add source file specific arguments."""
        args.extend(filter(lambda v: v is not None,
            [
                "--no-audio",
                "--no-video",
                "--no-subtitles",
                "--no-attachments" if not s.config.merge_src_file["copy_attachments"] else None,
                "--no-chapters" if not s.config.merge_src_file["copy_chapters"] else None,
                "--no-global-tags" if not s.config.merge_src_file["copy_global_tags"] else None,
                "--no-track-tags" if not s.config.merge_src_file["copy_track_tags"] else None,
                job.src_filepath
            ]
        ))

    @classmethod
    def _add_destination_file_args(cls, args, job: VideoSyncJob, encoded_audio_path: str | None = None) -> None:
        """Add destination file specific arguments."""
        audio_track_arg: list[str] = []
        selected_audio_stream: AudioStream = job.dst_streams.get_selected_audio_stream()
        if s.config.merge_dst_file["copy_only_selected_sync_audio_track"]:
            if encoded_audio_path:
                _track_lang: str = selected_audio_stream.lang if selected_audio_stream.lang else "und"
                audio_track_arg: list[str] = [
                    "--default-track",
                    "0:1",
                    "--language",
                    f"0:{_track_lang}",
                    encoded_audio_path,
                    "--no-audio", # Discard all original audio tracks from dst file since we're adding the encoded track as a new source
                ]
            elif selected_audio_stream.id is not None:
                audio_track_arg: list[str] = ["--audio-tracks", str(selected_audio_stream.id)]
        
        args.extend(filter(lambda v: v is not None,
            [
                *audio_track_arg,
                "--no-attachments" if not s.config.merge_dst_file["copy_attachments"] else None,
                "--no-chapters" if not s.config.merge_dst_file["copy_chapters"] else None,
                "--no-global-tags" if not s.config.merge_dst_file["copy_global_tags"] else None,
                "--no-subtitles" if not s.config.merge_dst_file["copy_subtitle_tracks"] else None,
                "--no-track-tags" if not s.config.merge_dst_file["copy_track_tags"] else None,
                job.dst_filepath
            ]
        ))

    @classmethod
    def _add_subtitle_args(cls, args, job: VideoSyncJob, use_resampled_sub: bool) -> None:
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

        args.extend([
            "--language", f"0:{job.src_streams.get_selected_subtitle_stream().lang}",
            "--track-name", f"0:{trackname}",
            "--default-track-flag",
            "0:0" if not s.config.merge_synced_sub_file["default_flag"] else "0:1",
            "--forced-display-flag",
            "0:0" if not s.config.merge_synced_sub_file["forced_flag"] else "0:1",
            f"{job.dst_filepath}{sub_suffix}"
        ])

    @classmethod
    def _get_merge_args(cls, job: VideoSyncJob, use_resampled_sub: bool = False, encoded_audio_path: str | None = None) -> list[str]:
        output_file: str = MKVMerge._get_out_filepath(job.dst_filepath)

        args: list[str] = [
            "mkvmerge",
            "--output",
            output_file,
        ]

        cls._add_source_file_args(args, job)
        cls._add_destination_file_args(args, job, encoded_audio_path)
        cls._add_subtitle_args(args, job, use_resampled_sub)
        return args

    @classmethod 
    def _show_warnings(cls, output: str, log_prefix: str, spinner: Yaspin | None = None) -> None:
        lines: list[str] = output.splitlines()
        warnings: str = "\n".join([line.replace("Warning: ", f"{log_prefix} Warning: ") for line in lines if line.startswith("Warning:")])
        if warnings:
            cu.try_print_spinner_message(f"{cu.fore.LIGHTYELLOW_EX}{warnings}\n", spinner)
           
    @classmethod
    def run(cls, job: VideoSyncJob, use_resampled_sub: bool = False, encoded_audio_path: str | None = None, spinner: Yaspin | None = None, log_prefix="[MKVMerge]", log_path: str | None = None) -> None:
        """Run MKVMerge and handle output logging. log_path can be provided to skip automatic log file creation."""
        try:     
            args: list[str] = cls._get_merge_args(job, use_resampled_sub, encoded_audio_path)
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
                args_log: str = f"{ExecutionLogger.internal_log_indicator}Running with arguments: {(' '.join(args))}\n\n" + stdout
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
