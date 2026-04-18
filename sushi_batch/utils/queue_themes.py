from ..models.enums import Task, Status, QueueTheme

from . import console_utils as cu


def _get_track_values(job):
    """Resolve track values using display label first, then raw id."""
    src_audio = job.src_aud_display if job.src_aud_display is not None else job.src_aud_id
    src_sub = job.src_sub_display if job.src_sub_display is not None else job.src_sub_id
    dst_audio = job.dst_aud_display if job.dst_aud_display is not None else job.dst_aud_id
    return src_audio, src_sub, dst_audio

def _has_any_track_data(job):
    """Return True when any source/sync target track metadata is available."""
    return any(
        value is not None
        for value in (
            job.src_aud_id,
            job.src_sub_id,
            job.dst_aud_id
        )
    )

def _get_sync_status_style(status):
    """Return display metadata for a job status."""
    match status:
        case Status.COMPLETED:
            return (cu.fore.LIGHTGREEN_EX, "Completed", "✓", cu.fore.GREEN)
        case Status.FAILED:
            return (cu.fore.LIGHTRED_EX, "Failed", "x", cu.fore.RED)
        case _:
            return (cu.fore.LIGHTYELLOW_EX, "Pending", "~", cu.fore.LIGHTYELLOW_EX)
        
def _merge_status_style(merge_status):
    """Return display metadata for a job's merge status."""
    match merge_status:
        case True:
            return (cu.fore.LIGHTGREEN_EX, "Completed", "✓", cu.fore.GREEN)
        case False:
            return (cu.fore.LIGHTYELLOW_EX, "Pending", "~", cu.fore.LIGHTYELLOW_EX)
        case _:
            return (cu.fore.LIGHTBLACK_EX, "Unknown", "?", cu.fore.LIGHTBLACK_EX)

def _show_classic_theme(queued_jobs, current_task):
    """ Show Job List contents (Classic Theme) """
    for idx, job in enumerate(queued_jobs, start=1):
        job.idx = idx
        print(f"\n{cu.fore.LIGHTBLACK_EX}Job {job.idx}")
        print(f"{cu.fore.LIGHTBLUE_EX}Source file: {job.src_file}")
        print(f"{cu.fore.YELLOW}Sync Target File: {job.dst_file}")

        if job.sub_file is not None:
            print(f"{cu.fore.LIGHTCYAN_EX }Subtitle file: {job.sub_file}")

        src_audio, src_sub, dst_audio = _get_track_values(job)

        if src_audio is not None:
            print(f"{cu.fore.LIGHTMAGENTA_EX}Source Audio Track: {src_audio}")

        if src_sub is not None:
            print(f"{cu.fore.LIGHTCYAN_EX}Source Subtitle Track: {src_sub}")

        if dst_audio is not None:
            print(f"{cu.fore.LIGHTMAGENTA_EX}Sync Target Audio Track: {dst_audio}")

        if current_task == Task.JOB_QUEUE: 
            match job.sync_status:
                case Status.PENDING:
                    print(f"{cu.fore.LIGHTYELLOW_EX}Sync Status: Pending")
                case Status.COMPLETED:
                    print(f"{cu.fore.LIGHTGREEN_EX}Sync Status: Completed")
                    print(f"{cu.fore.GREEN}Average Shift: {job.result}")
                case Status.FAILED:
                    print(f"{cu.fore.LIGHTRED_EX}Sync Status: Failed")
                    print(f"{cu.fore.RED}Error: {job.result}")

            match job.merged:
                case True:
                    print(f"{cu.fore.GREEN}Merged: Yes")
                case False:
                    print(f"{cu.fore.LIGHTYELLOW_EX}Merged: Pending")
                case _:
                    pass

def _show_card_theme(queued_jobs, current_task):
    """Show job list using card-style blocks (Card Theme)."""
    for idx, job in enumerate(queued_jobs, start=1):
        job.idx = idx
        status_color, status_label, status_icon, detail_color = _get_sync_status_style(job.sync_status)

        print(f"\n{cu.fore.LIGHTBLUE_EX}┌─ Job {idx}")

        src_audio, src_sub, dst_audio = _get_track_values(job)

        sections = [
            {
                "label": "Source",
                "value": f"{cu.fore.LIGHTBLUE_EX}{job.src_file}",
                "children": [
                    ("Audio Track", f"{cu.fore.LIGHTMAGENTA_EX}{src_audio}") if src_audio is not None else None,
                    ("Sub Track", f"{cu.fore.LIGHTCYAN_EX}{src_sub}") if src_sub is not None else None,
                ],
            },
            {
                "label": "Sync Target",
                "value": f"{cu.fore.YELLOW}{job.dst_file}",
                "children": [
                    ("Audio Track", f"{cu.fore.LIGHTMAGENTA_EX}{dst_audio}") if dst_audio is not None else None,
                ],
            },
        ]

        if job.sub_file is not None:
            sections.append(
                {
                    "label": "Subtitle",
                    "value": f"{cu.fore.LIGHTCYAN_EX}{job.sub_file}",
                }
            )

        if current_task == Task.JOB_QUEUE:
            status_section = {
                "label": "Sync Status",
                "value": f"{status_color}{status_icon} {status_label}",
                "children": [],
            }
            if job.sync_status == Status.COMPLETED:
                status_section["children"].append(("Avg Shift", f"{detail_color}{job.result}"))
            elif job.sync_status == Status.FAILED:
                status_section["children"].append(("Error", f"{detail_color}{job.result}"))
            sections.append(status_section)

            if job.merged is not None and job.sync_status == Status.COMPLETED:
                merged_color, merged_label, merged_icon, merged_child_color = _merge_status_style(job.merged)

                sections.append(
                    {
                        "label": "Merge Status",
                        "value": merged_color + merged_icon + " " + merged_label,
                        "children": [
                            ("Generated File", f"{merged_child_color}{job.merged_file}") if job.merged_file is not None else None,
                            ("Resampled", f"{merged_child_color}Yes") if job.resample_done else None,
                        ],
                    }
                )
        
        sections = [
            {
                "label": section["label"],
                "value": section["value"],
                "children": [child for child in section.get("children", []) if child is not None],
            }
            for section in sections
        ]

        last_section_idx = len(sections) - 1
        for sec_idx, section in enumerate(sections):
            is_last_section = sec_idx == last_section_idx
            top_divider = "└─" if is_last_section else "├─"
            print(f"{cu.fore.LIGHTBLACK_EX}{top_divider} {section['label']}: {section['value']}")

            children = section["children"]
            for child_idx, (child_label, child_value) in enumerate(children):
                is_last_child = child_idx == len(children) - 1
                child_prefix = "   " if is_last_section else "│  "
                child_divider = "└─" if is_last_child else "├─"
                print(f"{cu.fore.LIGHTBLACK_EX}{child_prefix}{child_divider} {child_label}: {child_value}")

def _show_yaml_like_theme(queued_jobs, current_task):
    """Show job list in a YAML/config style format (YAML-like Theme)."""
    for idx, job in enumerate(queued_jobs, start=1):
        job.idx = idx
        status_color, status_label, _, detail_color = _get_sync_status_style(job.sync_status)

        print(f"\n{cu.fore.LIGHTBLUE_EX}Job {idx}:")
        print(f"{cu.fore.LIGHTBLACK_EX}  source_file: {cu.fore.LIGHTBLUE_EX}{job.src_file}")
        print(f"{cu.fore.LIGHTBLACK_EX}  sync_target_file: {cu.fore.YELLOW}{job.dst_file}")
        
        if job.sub_file is not None:
            print(f"{cu.fore.LIGHTBLACK_EX}  subtitle_file: {cu.fore.LIGHTCYAN_EX}{job.sub_file}")

        show_tracks_section = _has_any_track_data(job)

        if show_tracks_section:
            src_audio, src_sub, dst_audio = _get_track_values(job)

            print(f"{cu.fore.LIGHTBLACK_EX}  tracks:")
            print(f"{cu.fore.LIGHTBLACK_EX}    source_audio: {cu.fore.LIGHTMAGENTA_EX}{src_audio if src_audio is not None else 'null'}")
            print(f"{cu.fore.LIGHTBLACK_EX}    source_subtitle: {cu.fore.LIGHTCYAN_EX}{src_sub if src_sub is not None else 'null'}")
            print(f"{cu.fore.LIGHTBLACK_EX}    sync_target_audio: {cu.fore.LIGHTMAGENTA_EX}{dst_audio if dst_audio is not None else 'null'}")

        if current_task == Task.JOB_QUEUE:
            print(f"{cu.fore.LIGHTBLACK_EX}  sync_status: {status_color}{status_label.lower()}")
            if job.sync_status == Status.FAILED:
                print(f"{cu.fore.LIGHTBLACK_EX}  error: {detail_color}{job.result}")
            elif job.sync_status == Status.COMPLETED:
                print(f"{cu.fore.LIGHTBLACK_EX}  average_shift: {detail_color}{job.result}")
                match job.merged:
                    case True:
                        merge_color, merge_label, _, merge_child_color = _merge_status_style(job.merged)
                        print(f"{cu.fore.LIGHTBLACK_EX}  merge_status: {merge_color}{merge_label.lower()}")
                        if job.merged_file:
                            print(f"{cu.fore.LIGHTBLACK_EX}  merged_file: {merge_child_color}{job.merged_file}")
                        if job.resample_done:
                            print(f"{cu.fore.LIGHTBLACK_EX}  resampled: {merge_child_color}true")
                    case False:
                        print(f"{cu.fore.LIGHTYELLOW_EX}  merge_status: pending")
                    case _:
                        pass
            

QUEUE_RENDERERS = {
    QueueTheme.CLASSIC: _show_classic_theme,
    QueueTheme.CARD: _show_card_theme,
    QueueTheme.YAML: _show_yaml_like_theme,
}