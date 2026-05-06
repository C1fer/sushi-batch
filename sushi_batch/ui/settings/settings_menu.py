from enum import Enum
from typing import Iterable, NotRequired, TypedDict

from prettytable import PrettyTable

from ...models.enums import AudioEncodeCodec, QueueTheme, Section, TracksToEncode
from ...models.settings import Settings
from ...utils import console_utils as cu
from ...utils import file_utils as fu
from ...utils.constants import DynamicMenuItem, MenuItem, SelectableOption
from ..prompts import choice_prompt, confirm_prompt, input_prompt
from ..settings.encode_codec_settings_menu import configure_audio_encode_settings
from ..settings.sushi_advanced_args_menu import configure_advanced_sushi_args

GO_BACK_OPTION_LABEL: str = "Go Back"

type OptionValue = bool | QueueTheme | AudioEncodeCodec | TracksToEncode | str | None
class SettingsRow(TypedDict):
    section: Section
    label: str
    attr: str
    value: OptionValue
    description: str
    show: bool
    divider: NotRequired[bool]


MENU_OPTIONS: list[MenuItem | DynamicMenuItem] = [
    (1, "Change a Setting"),
    (2, "Configure Advanced Sushi Arguments", lambda validations: validations.get("enable_advanced_sushi_args")),
    (3, "Configure Audio Encode Settings", lambda validations: validations.get("encode_lossless_audio_before_merging")),
    (4, "Restore Default Settings"),
    (5, "Clear Logs"),
    (6, "View Settings Help"),
    (7, "Return to Main Menu")
]

SECTION_SUB_OPTIONS: list[MenuItem] = [
    (1, Section.GEN.value),
    (2, Section.SYNC.value),
    (3, Section.MERGE_WRK.value),
    (4, Section.MERGE_SRC.value),
    (5, Section.MERGE_DST.value),
    (6, Section.MERGE_SUB.value),
    (7, GO_BACK_OPTION_LABEL)
]


def _get_formatted_value(value: OptionValue) -> str:
    """Return formatted value for table display"""
    match value:
        case True:
            return f"{cu.Fore.GREEN}Enabled{cu.style_reset}"
        case False:
            return f"{cu.Fore.RED}Disabled{cu.style_reset}"
        case QueueTheme() | AudioEncodeCodec() | TracksToEncode():
            return f"{cu.Fore.MAGENTA}{value.value}{cu.style_reset}"
        case _:
            _color = cu.Fore.YELLOW if value else cu.Fore.LIGHTBLACK_EX
            _value = value if value else "Not set"
            return f"{_color}{_value}{cu.style_reset}"
        
def _get_settings_rows(obj: Settings) -> list[SettingsRow]:
    """Return the settings rows used by the table and selection flow."""
    rows: list[SettingsRow] = [
        # General Section
        {
            "section": Section.GEN,
            "label": "Queue Theme",
            "attr": "general.queue_theme",
            "value": obj.general["queue_theme"],
            "description": "Controls how queued jobs are displayed in the terminal queue view.",
            "show": True,
        },
        {
            "section": Section.GEN,
            "label": "Save Sushi Sync Logs",
            "attr": "general.save_sushi_logs",
            "value": obj.general["save_sushi_logs"],
            "description": "Save logs for each subtitle sync operation.",
            "show": True,
        },
        {
            "section": Section.GEN,
            "label": "Save Merge Logs",
            "attr": "general.save_merge_logs",
            "value": obj.general["save_merge_logs"],
            "divider": True,
            "description": "Saves logs for each merge operation.",
            "show": True,
        },

        # Subtitle Sync Section
        {
            "section": Section.SYNC,
            "label": "Use High Quality Resampling (Improved Accuracy)",
            "attr": "sync_workflow.use_high_quality_resample",
            "value": obj.sync_workflow["use_high_quality_resample"],
            "description": "Use 24 kHz resampling during sync for potentially better timing accuracy. Can increase processing time.",
            "show": True,
        },
        {
            "section": Section.SYNC,
            "label": "Allow Advanced Sushi Arguments",
            "attr": "sync_workflow.enable_sushi_advanced_args",
            "value": obj.sync_workflow["enable_sushi_advanced_args"],
            "divider": True,
            "description": "Enables custom Sushi argument overrides for advanced synchronization tuning.",
            "show": True,
        },

        # Merge - Workflow Section
        {
            "section": Section.MERGE_WRK,
            "label": "Merge Automatically on Sync Completion",
            "attr": "merge_workflow.merge_files_after_execution",
            "value": obj.merge_workflow["merge_files_after_execution"],
            "description": "Starts merge automatically after sync completes successfully (Requires MKVMerge).",
            "show": True,
        },
        {
            "section": Section.MERGE_WRK,
            "label": "Encode Lossless Sync Target Audio Track Before Merge",
            "attr": "merge_workflow.encode_lossless_audio_before_merging",
            "value": obj.merge_workflow["encode_lossless_audio_before_merging"],
            "description": "Re-encode selected lossless tracks to the chosen codec before merging.",
            "show": True,
        },
        {
            "section": Section.MERGE_WRK,
            "label": "Tracks to Encode Before Merging",
            "attr": "merge_workflow.tracks_to_encode_before_merging",
            "value": obj.merge_workflow["tracks_to_encode_before_merging"],
            "description": "Defines which audio tracks to encode before merging when pre-merge audio encoding is enabled.",
            "show":bool(obj.merge_workflow["encode_lossless_audio_before_merging"] and not obj.merge_dst_file["copy_only_selected_sync_audio_track"]),
        },
        {
            "section": Section.MERGE_WRK,
            "label": "Audio Encode Codec",
            "attr": "merge_workflow.encode_codec",
            "value": obj.merge_workflow["encode_codec"],
            "description": "Target lossy codec for re-encoding when pre-merge audio encoding is enabled. Current supported codecs are AAC, EAC-3 and Opus.",
            "show": obj.merge_workflow["encode_lossless_audio_before_merging"],
        },
        {
            "section": Section.MERGE_WRK,
            "label": "Resample Synced Sub Before Merge",
            "attr": "merge_workflow.resample_subs_on_merge",
            "value": obj.merge_workflow["resample_subs_on_merge"],
            "description": "Resample synced subtitle to match target video resolution before merging (Requires Aegisub-CLI).",
            "show": True,
        },
        {
            "section": Section.MERGE_WRK,
            "label": "Delete Generated Audio/Subtitle Files After Merge",
            "attr": "merge_workflow.delete_generated_files_after_merge",
            "value": obj.merge_workflow["delete_generated_files_after_merge"],
            "divider": True,
            "description": "Remove temporary generated subtitle/audio files automatically after merge completes.",
            "show": True,
        },

        # Merge: Source File Section
        {
            "section": Section.MERGE_SRC,
            "label": "Copy Attachments",
            "attr": "merge_src_file.copy_attachments",
            "value": obj.merge_src_file["copy_attachments"],
            "description": "Copy attachments (fonts, cover art) from the source file into the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_SRC,
            "label": "Copy Chapters",
            "attr": "merge_src_file.copy_chapters",
            "value": obj.merge_src_file["copy_chapters"],
            "description": "Copy chapter entries from the source file into the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_SRC,
            "label": "Copy Global Tags",
            "attr": "merge_src_file.copy_global_tags",
            "value": obj.merge_src_file["copy_global_tags"],
            "description": "Copy container-level tags from the source file into the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_SRC,
            "label": "Copy Track Tags",
            "attr": "merge_src_file.copy_track_tags",
            "value": obj.merge_src_file["copy_track_tags"],
            "divider": True,
            "description": "Copy per-track metadata tags from the source file into the merged output.",
            "show": True,
        },

        # Merge: Sync Target File Section
        {
            "section": Section.MERGE_DST,
            "label": "Only Include Track Used for Sync",
            "attr": "merge_dst_file.copy_only_selected_sync_audio_track",
            "value": obj.merge_dst_file["copy_only_selected_sync_audio_track"],
            "description": "Exclude all audio tracks from the target file except the one used for sync.",
            "show": True,
        },
        {
            "section": Section.MERGE_DST,
            "label": "Copy Attachments",
            "attr": "merge_dst_file.copy_attachments",
            "value": obj.merge_dst_file["copy_attachments"],
            "description": "Copy attachments (fonts, cover art) from the target file into the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_DST,
            "label": "Copy Chapters",
            "attr": "merge_dst_file.copy_chapters",
            "value": obj.merge_dst_file["copy_chapters"],
            "description": "Copy chapter entries from the target file into the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_DST,
            "label": "Copy Subtitles",
            "attr": "merge_dst_file.copy_subtitle_tracks",
            "value": obj.merge_dst_file["copy_subtitle_tracks"],
            "description": "Copy subtitle tracks from the target file in addition to the synced subtitle.",
            "show": True,
        },
        {
            "section": Section.MERGE_DST,
            "label": "Copy Global Tags",
            "attr": "merge_dst_file.copy_global_tags",
            "value": obj.merge_dst_file["copy_global_tags"],
            "description": "Copy container-level tags from the target file into the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_DST,
            "label": "Copy Track Tags",
            "attr": "merge_dst_file.copy_track_tags",
            "value": obj.merge_dst_file["copy_track_tags"],
            "divider": True,
            "description": "Copy per-track metadata tags from the target file into the merged output.",
            "show": True,
        },

        # Merge: Synced Subtitle Section
        {
            "section": Section.MERGE_SUB,
            "label": "Set as Default Track",
            "attr": "merge_synced_sub_file.default_flag",
            "value": obj.merge_synced_sub_file["default_flag"],
            "description": "Mark the merged synced subtitle track as default in the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_SUB,
            "label": "Set as Forced Track",
            "attr": "merge_synced_sub_file.forced_flag",
            "value": obj.merge_synced_sub_file["forced_flag"],
            "description": "Mark the merged synced subtitle track as forced in the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_SUB,
            "label": "Override Track Title",
            "attr": "merge_synced_sub_file.custom_trackname",
            "value": obj.merge_synced_sub_file["custom_trackname"],
            "description": "Enables overriding the default track title for the merged synced subtitle track.",
            "show": True,
        },
        {
            "section": Section.MERGE_SUB,
            "label": "Custom Track Title",
            "attr": "merge_synced_sub_file.trackname",
            "value": obj.merge_synced_sub_file["trackname"],
            "description": "Custom title for the merged synced subtitle track when override is enabled.",
            "show": obj.merge_synced_sub_file["custom_trackname"],
        },
    ]

    return [row for row in rows if row["show"]]

def _render_settings_table(rows: list[SettingsRow]) -> PrettyTable:
    """Create and return settings table"""
    tb = PrettyTable(["Section", "Name", "Value"])
    
    for row in rows:
        if not row["show"]:
            continue

        tb.add_row(
            [row["section"].value, row["label"], 
            _get_formatted_value(row["value"])],
            divider=row.get("divider", False)
        )
    
    return tb

def _select_from_enum[T:Enum](enum: Iterable[T]) -> T | None:
    """Display options for an enum and return the selected item"""
    options: list[SelectableOption] = [(idx, item.value) for idx, item in enumerate(enum, 1)]
    options.append((len(options) + 1, GO_BACK_OPTION_LABEL))

    choice_idx: int = choice_prompt.get(options=options, nl_before=False, nl_after=False)
    if choice_idx == len(options): # Go Back option selected
        return None

    return next(item for item in enum if item.value == options[choice_idx - 1][1])

def _update_value(obj: Settings, option: str) -> None:
    """Update value for selected option (handles both direct attributes and nested dict options)"""
    attr_path: list[str] = option.split(".")
    parent_attr_key: str = attr_path[0]
    option_key: str = attr_path[1]
    parent: dict[str, OptionValue] = getattr(obj, parent_attr_key)
    
    curr_val: OptionValue = parent.get(option_key)
    new_val: OptionValue = None
    print(f"Current value: {_get_formatted_value(curr_val)}\n")
    
    match curr_val:
        case QueueTheme():
            new_val: QueueTheme | None = _select_from_enum(QueueTheme)
        case AudioEncodeCodec():
            new_val: AudioEncodeCodec | None = _select_from_enum(AudioEncodeCodec)
        case TracksToEncode():
            new_val: TracksToEncode | None = _select_from_enum(TracksToEncode)
        case bool():
            prompt: str = "Disable" if curr_val else "Enable"
            if confirm_prompt.get(f"{prompt} option?"):
                new_val: bool = not curr_val  
        case str():
            user_input: str = input_prompt.get(allow_empty=True)
            if confirm_prompt.get():
                new_val: str = user_input
                
    if new_val is not None and new_val != curr_val:
        parent[option_key] = new_val
        obj.handle_save()

def _handle_option_choice(section_options: list[SelectableOption]) -> int | None:
    """Handle user choice for setting inside a section"""
    go_back_id: int = len(section_options) + 1
    options: list[SelectableOption] = section_options + [(go_back_id, GO_BACK_OPTION_LABEL)]

    selected_option_id: int = choice_prompt.get("Select setting to modify: ", options)
    if selected_option_id == go_back_id:
        return None # Go Back option selected at option level

    return next(idx for idx, _ in options if idx == selected_option_id)

def _select_setting_to_update(rows: list[SettingsRow]) -> str | None:
    """Prompt user to select a setting to update and return the corresponding attribute name"""
    while True:
        selected_section_idx: int = choice_prompt.get("Select section: ", options=SECTION_SUB_OPTIONS, nl_after=False)
        
        section_val: str = SECTION_SUB_OPTIONS[selected_section_idx - 1][1]
        if section_val == GO_BACK_OPTION_LABEL:
            return None # Go Back option selected at section level
        
        option_idx: int = 1
        section_options: list[SelectableOption] = []
        for row in rows:
            if row["section"].value == section_val:
                section_options.append((option_idx, row["label"]))
                option_idx += 1
        
        selected_option: int | None = _handle_option_choice(section_options)
        if selected_option:
            return next(row["attr"] for row in rows if row["label"] == section_options[selected_option - 1][1])

def _view_settings_help(visible_rows: list[SettingsRow]) -> None:
    """Display help text for each section and setting"""
    cu.clear_screen()
    cu.print_header("Settings Help", nl_after=True)
    
    settings_by_section: dict[Section, list[SettingsRow]] = {
        section: [row for row in visible_rows if row["section"] == section]
        for section in Section
    }

    for section, settings in settings_by_section.items():
        section_title = f" {section.value} "
        section_divider:str = "=" * max(8, 56 - len(section_title))
        print(f"{cu.Fore.LIGHTMAGENTA_EX}{section_divider}{section_title}{section_divider}{cu.style_reset}")
        for setting in settings:
            cu.print_help_text(setting["label"], setting["description"])
        print()
    input_prompt.get("Press Enter to close...  ", allow_empty=True, nl_before=True)
    

def show_settings_menu(settings_obj: Settings) -> None:
    """Display and handle options in new menu"""
    while True:
        cu.clear_screen()
        cu.print_header("App Settings\n")
        visible_rows: list[SettingsRow] = _get_settings_rows(settings_obj)
        tbl: PrettyTable = _render_settings_table(visible_rows)
        print(tbl)

        validations: dict[str, bool] = {
            "enable_advanced_sushi_args": bool(settings_obj.sync_workflow["enable_sushi_advanced_args"]),
            "encode_lossless_audio_before_merging": bool(settings_obj.merge_workflow["encode_lossless_audio_before_merging"]),
        }

        menu_options: list[MenuItem] = cu.get_visible_options(MENU_OPTIONS, validations)
        choice: int = choice_prompt.get(options=menu_options, nl_after=False)
        match choice:
            case 1:
                selected: str | None = _select_setting_to_update(visible_rows)
                if selected:
                    _update_value(settings_obj, selected)
            case 2:
                configure_advanced_sushi_args(settings_obj)
            case 3:
                current_codec: AudioEncodeCodec = settings_obj.merge_workflow["encode_codec"]
                configure_audio_encode_settings(settings_obj, current_codec)
            case 4:
                if confirm_prompt.get(nl_before=True, destructive=True):
                    settings_obj.restore()
                    cu.print_success("Settings restored to default values.")
            case 5:
                if confirm_prompt.get("Are you sure you want to clear the logs? This action cannot be undone.", nl_before=True, destructive=True):
                    fu.clear_logs(settings_obj.data_path)
                    cu.print_success("Logs cleared.")
                    break
            case 6:
                _view_settings_help(visible_rows)
            case _:
                break