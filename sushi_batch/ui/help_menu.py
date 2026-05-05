from ..utils import console_utils as cu
from .prompts import input_prompt


def show_help_screen() -> None:
    """Display app usage and navigation help."""
    cu.clear_screen()
    cu.print_header("Help\n")

    help_lines: list[str] = [
        f"{cu.fore.YELLOW}Overview{cu.style_reset}",
        "This tool allows for batch processing of subtitle sync jobs, among other features.",

        f"\n{cu.fore.YELLOW}Main Features{cu.style_reset}",
        "- Sync subtitle timing between different releases of the same media (e.g., WEB-DL to Blu-Ray) without the need for manual adjustments. Ideal for anime fansub releases but can be used for any media with existing subtitles.",
        "- [Video Sync Jobs] Merge the synced subtitles back into the target video file after syncing (requires MKVMerge).",
        "- [Video Sync Jobs] Resample synced subtitles to match the resolution of the target video (requires Aegisub-CLI).",
        "- [Video Sync Jobs] Encode lossless audio tracks from target file to a lossy format (e.g., AAC, OPUS) during merge.",

        f"\n{cu.fore.YELLOW}How to Use{cu.style_reset}",
        "1. Create a new sync job by selecting the source and target files or directories.",
        "2. For video sync jobs, choose the audio and subtitle tracks to use for syncing.",
        "3. Press 'Run Job' to execute the sync.",
        "4. After sync completion, the synced subtitle will be available in the same directory as the target file.",
        "5. If enabled in settings and MKVMerge is available, a new video file will be created with the synced subtitle. This file will be located in the 'Merged Files' folder within the target's directory.",

        f"\n{cu.fore.YELLOW}Terminology{cu.style_reset}",
        "- Source File: The original video or audio file that contains the subtitle you want to sync.",
        "- Target File: The video or audio file that you want to sync the subtitle with.",
        "- Sync Job: A task that coordinates the synchronization of a subtitle between the source and target file.",
        
        f"\n{cu.fore.YELLOW}Supported Formats{cu.style_reset}",
        "- Video Sync: Common video formats (e.g., MKV, MP4) and subtitle formats (e.g., ASS, SRT).",
        "- Audio Sync: Common audio formats (e.g., FLAC, OPUS, AAC, AC3).",

        f"\n{cu.fore.YELLOW}App Information{cu.style_reset}",
        "- Data and logs for all enabled operations are stored in the 'SushiBatchTool' directory inside your Documents folder.",

        f"\n{cu.fore.YELLOW}Download Links for Optional Dependencies{cu.style_reset}",
        f"- MKVMerge (for video merging): {cu.fore.LIGHTBLUE_EX}https://mkvtoolnix.download/downloads.html{cu.style_reset}",
        f"- Aegisub-CLI (for subtitle resampling): {cu.fore.LIGHTBLUE_EX}https://github.com/Myaamori/aegisub-cli{cu.style_reset}",
        f"- Opus-tools (alternative to FFmpeg for Opus encoding): {cu.fore.LIGHTBLUE_EX}https://www.videohelp.com/software/OpusTools{cu.style_reset}",
    ]
    print("\n".join(help_lines))

    input_prompt.get("Press Enter to return to the main menu... ", allow_empty=True, nl_before=True)