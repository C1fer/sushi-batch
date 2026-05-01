import re
from typing import Callable,TypedDict

from ..external.sub_sync import Sushi
from ..models.enums import AudioEncodeCodec, AudioEncoder, QueueTheme, Status
from ..models.job.audio_sync_job import AudioSyncJob
from ..models.job.video_sync_job import VideoSyncJob
from ..models.job_queue import JobQueueContents
from ..utils import console_utils as cu
from ..utils.console_utils import ConsoleColor

class CardDisplaySection(TypedDict):
    label: str
    value: str
    children: list[tuple[str, str] | None]

SYNC_COMPLETED_WARNING = f"{cu.Fore.LIGHTYELLOW_EX}Sync completed with warnings. Check Sushi log for details."
SYNC_EXCEED_WARNING = f"{cu.fore.LIGHTYELLOW_EX}High average shift detected. Check synced subtitle for accuracy."
MERGE_WARNING_MESSAGE = f"{cu.fore.LIGHTYELLOW_EX}Merge completed with warnings. Check mkvmerge log for details."


def _avg_shift_exceeds_threshold(sushi_result: str) -> bool:
    """Determine if the average shift exceeds the defined safe threshold."""
    try:
        shift_val = float(re.sub(r"[^0-9.\-]", "", sushi_result))
        return abs(shift_val) > Sushi.max_safe_avg_shift
    except ValueError:
        return False
    
def _get_encode_info_display(job: VideoSyncJob) -> str:
    """Format the display string for the audio encoding information (codec and bitrate)."""
    encoder_name: str = AudioEncoder[job.merge.audio_encode_encoder].value if job.merge.audio_encode_encoder else "Unknown Encoder"
    codec_name: str = AudioEncodeCodec[job.merge.audio_encode_codec].value if job.merge.audio_encode_codec else "Unknown Codec"
    return f"({codec_name} - {job.merge.audio_encode_bitrate}) [{encoder_name}]"

def _get_sync_status_style(status: Status) -> tuple[ConsoleColor, str, str, ConsoleColor]:
    """Return display metadata for a job status."""
    match status:
        case Status.COMPLETED:
            return (cu.fore.LIGHTGREEN_EX, "Completed", "✓", cu.fore.GREEN)
        case Status.FAILED:
            return (cu.fore.LIGHTRED_EX, "Failed", "x", cu.fore.RED)
        case _:
            return (cu.fore.LIGHTYELLOW_EX, "Pending", "~", cu.fore.LIGHTYELLOW_EX)
        
def _merge_status_style(merge_status: bool) -> tuple[ConsoleColor, str, str, ConsoleColor]:
    """Return display metadata for a job's merge status."""
    return (
        (cu.fore.LIGHTGREEN_EX, "Completed", "✓", cu.fore.GREEN)
        if merge_status
        else (cu.fore.LIGHTYELLOW_EX, "Pending", "~", cu.fore.LIGHTYELLOW_EX)
    )

def _show_classic_theme(queued_jobs: JobQueueContents, is_main_queue: bool = True) -> None:
    """ Show Job List contents (Classic Theme) """
    for idx, job in enumerate(queued_jobs, start=1):
        job.id = idx
        print(f"\n{cu.fore.LIGHTBLACK_EX}Job {job.id}")
        print(f"{cu.fore.LIGHTBLUE_EX}Source file: {job.src_filepath}")
        print(f"{cu.fore.YELLOW}Sync Target File: {job.dst_filepath}")

        if isinstance(job, AudioSyncJob):
            print(f"{cu.fore.LIGHTCYAN_EX }Subtitle file: {job.sub_filepath}")

        elif isinstance(job, VideoSyncJob):
            print(f"{cu.fore.LIGHTMAGENTA_EX}Source Audio Track: {job.src_streams.get_selected_audio_stream().display_label}")
            print(f"{cu.fore.LIGHTCYAN_EX}Source Subtitle Track: {job.src_streams.get_selected_subtitle_stream().display_label}")
            print(f"{cu.fore.LIGHTMAGENTA_EX}Sync Target Audio Track: {job.dst_streams.get_selected_audio_stream().display_label}")

        if is_main_queue: 
            match job.sync.status:
                case Status.PENDING:
                    print(f"{cu.fore.LIGHTYELLOW_EX}Sync Status: Pending")
                case Status.COMPLETED:
                    print(f"{cu.fore.LIGHTGREEN_EX}Sync Status: Completed")
                    print(f"{cu.fore.GREEN}Average Shift: {job.sync.result}")
                case Status.FAILED:
                    print(f"{cu.fore.LIGHTRED_EX}Sync Status: Failed")
                    print(f"{cu.fore.RED}Error: {job.sync.result}")

            if isinstance(job, VideoSyncJob):
                match job.merge.done:
                    case True:
                        print(f"{cu.fore.GREEN}Merged: Yes")
                    case False:
                        print(f"{cu.fore.LIGHTYELLOW_EX}Merged: Pending")
                    case _:
                        pass

def _show_card_theme(queued_jobs: JobQueueContents, is_main_queue: bool = True) -> None:
    """Show job list using card-style blocks (Card Theme)."""
    for idx, job in enumerate(queued_jobs, start=1):
        job.id = idx
        print(f"\n{cu.fore.LIGHTBLUE_EX}┌─ Job {idx}")
        
        sections: list[CardDisplaySection] = [
            {
                "label": "Source",
                "value": f"{cu.fore.LIGHTBLUE_EX}{job.src_filepath}",
                "children": [
                    ("Audio Track", f"{cu.fore.LIGHTMAGENTA_EX}{job.src_streams.get_selected_audio_stream().display_label}"),
                    ("Sub Track", f"{cu.fore.LIGHTCYAN_EX}{job.src_streams.get_selected_subtitle_stream().display_label}"),
                ] if isinstance(job, VideoSyncJob) else [],
            },
            {
                "label": "Sync Target",
                "value": f"{cu.fore.YELLOW}{job.dst_filepath}",
                "children": [
                    ("Audio Track", f"{cu.fore.LIGHTMAGENTA_EX}{job.dst_streams.get_selected_audio_stream().display_label}"),
                ] if isinstance(job, VideoSyncJob) else [],
            },
        ]

        if isinstance(job, AudioSyncJob):
            sections.append(
                {
                    "label": "Subtitle",
                    "value": f"{cu.fore.LIGHTCYAN_EX}{job.sub_filepath}",
                    "children": [],
                }
            )

        if is_main_queue:
            status_color, status_label, status_icon, detail_color = _get_sync_status_style(job.sync.status)
            sections.append(
                {
                    "label": "Sync Status",
                    "value": f"{status_color}{status_icon} {status_label}",
                    "children": [
                        ("Average Shift", f"{detail_color}{job.sync.result}") if job.sync.status == Status.COMPLETED else None,           
                        ("Sync Warning", SYNC_COMPLETED_WARNING) if job.sync.has_warnings else None,
                        ("Shift Warning", SYNC_EXCEED_WARNING) if job.sync.status == Status.COMPLETED and job.sync.result and _avg_shift_exceeds_threshold(job.sync.result) else None,
                        ("Error", f"{detail_color}{job.sync.result}") if job.sync.status == Status.FAILED else None,
                    ],
                }
            )

            if isinstance(job, VideoSyncJob) and job.merge.done is not None and job.sync.status == Status.COMPLETED:
                merged_color, merged_label, merged_icon, merged_child_color = _merge_status_style(job.merge.done)
                sections.append(
                    {
                        "label": "Merge Status",
                        "value": f"{merged_color}{merged_icon} {merged_label}",
                        "children": [
                            ("Generated File", f"{merged_child_color}{job.merge.merged_filepath}"),
                            ("Warning", MERGE_WARNING_MESSAGE) if job.merge.has_warnings else None,
                            ("Resampled", f"{cu.fore.GREEN}Yes") if job.merge.resample_done else None,
                            ("Encoded Audio", f"{cu.fore.GREEN}Yes {_get_encode_info_display(job)}") if job.merge.audio_encode_done else None, 
                        ] if job.merge.done and job.merge.merged_filepath else [],
                    }
                )
        
        last_section_idx = len(sections) - 1
        for sec_idx, section in enumerate[CardDisplaySection](sections):
            is_last_section: bool = sec_idx == last_section_idx
            top_divider: str = "└─" if is_last_section else "├─"
            print(f"{cu.fore.LIGHTBLACK_EX}{top_divider} {section['label']}: {section['value']}")

            visible_children: list[tuple[str,str]] = [child for child in section["children"] if child is not None]
            if not visible_children:
                continue
            
            for child_idx, (child_label, child_value) in enumerate(visible_children):
                is_last_child: bool = child_idx == len(visible_children) - 1
                child_prefix: str = "   " if is_last_section else "│  "
                child_divider: str = "└─" if is_last_child else "├─"
                print(f"{cu.fore.LIGHTBLACK_EX}{child_prefix}{child_divider} {child_label}: {child_value}")

def _show_yaml_like_theme(queued_jobs: JobQueueContents, is_main_queue: bool = True) -> None:
    """Show job list in a YAML/config style format (YAML-like Theme)."""
    for idx, job in enumerate(queued_jobs, start=1):
        job.id = idx
        status_color, status_label, _, detail_color = _get_sync_status_style(job.sync.status)

        print(f"\n{cu.fore.LIGHTBLUE_EX}Job {idx}:")
        print(f"{cu.fore.LIGHTBLACK_EX}  source_file: {cu.fore.LIGHTBLUE_EX}{job.src_filepath}")
        print(f"{cu.fore.LIGHTBLACK_EX}  sync_target_file: {cu.fore.YELLOW}{job.dst_filepath}")
        
        if isinstance(job, AudioSyncJob):
            print(f"{cu.fore.LIGHTBLACK_EX}  subtitle_file: {cu.fore.LIGHTCYAN_EX}{job.sub_filepath}")


        if isinstance(job, VideoSyncJob):
            print(f"{cu.fore.LIGHTBLACK_EX}  tracks:")
            print(f"{cu.fore.LIGHTBLACK_EX}    source_audio: {cu.fore.LIGHTMAGENTA_EX}{job.src_streams.get_selected_audio_stream().display_label}")
            print(f"{cu.fore.LIGHTBLACK_EX}    source_subtitle: {cu.fore.LIGHTCYAN_EX}{job.src_streams.get_selected_subtitle_stream().display_label}")
            print(f"{cu.fore.LIGHTBLACK_EX}    sync_target_audio: {cu.fore.LIGHTMAGENTA_EX}{job.dst_streams.get_selected_audio_stream().display_label}")

        if is_main_queue:
            print(f"{cu.fore.LIGHTBLACK_EX}  sync_status: {status_color}{status_label.lower()}")
            if job.sync.status == Status.FAILED:
                print(f"{cu.fore.LIGHTBLACK_EX}  error: {detail_color}{job.sync.result}")
            elif job.sync.status == Status.COMPLETED:
                print(f"{cu.fore.LIGHTBLACK_EX}  average_shift: {detail_color}{job.sync.result}")
                if job.sync.has_warnings:
                    print(f"{cu.fore.LIGHTBLACK_EX}  sync_warning: {SYNC_COMPLETED_WARNING}")
                if job.sync.result and _avg_shift_exceeds_threshold(job.sync.result):
                    print(f"{cu.fore.LIGHTBLACK_EX}  shift_warning: {SYNC_EXCEED_WARNING}")
                
                if isinstance(job, VideoSyncJob):
                    if job.merge.done:
                        merge_color, merge_label, _, merge_child_color = _merge_status_style(job.merge.done)
                        print(f"{cu.fore.LIGHTBLACK_EX}  merge_status: {merge_color}{merge_label.lower()}")
                        if job.merge.has_warnings:
                            print(f"{cu.fore.LIGHTBLACK_EX}  merge_warning: {MERGE_WARNING_MESSAGE}")
                        if job.merge.merged_filepath:
                            print(f"{cu.fore.LIGHTBLACK_EX}  merged_file: {merge_child_color}{job.merge.merged_filepath}")
                        if job.merge.resample_done:
                            print(f"{cu.fore.LIGHTBLACK_EX}  resampled: {cu.fore.GREEN}true")
                        if job.merge.audio_encode_done:
                            print(f"{cu.fore.LIGHTBLACK_EX}  audio_encoded: {cu.fore.GREEN}true {_get_encode_info_display(job)}")
                    else:
                        print(f"{cu.fore.LIGHTYELLOW_EX}  merge_status: pending")


QUEUE_RENDERERS: dict[QueueTheme, Callable[[JobQueueContents, bool], None]] = {
    QueueTheme.CLASSIC: _show_classic_theme,
    QueueTheme.CARD: _show_card_theme,
    QueueTheme.YAML: _show_yaml_like_theme,
}