from prettytable import PrettyTable

from .prompts import choice_prompt, confirm_prompt, input_prompt
from .sushi_advanced_args_menu import configure_advanced_sushi_args
from.encode_codec_settings_menu import configure_audio_encode_settings

from ..models.settings import Settings

from ..utils import console_utils as cu
from ..utils import file_utils as fu
from ..models.enums import AudioEncodeCodec, Section, QueueTheme

GO_BACK_OPTION_LABEL = "Go Back"

QUEUE_THEMES = {
    QueueTheme.CLASSIC: "Classic",
    QueueTheme.CARD: "Card",
    QueueTheme.YAML: "YAML-inspired"
}

MENU_OPTIONS = [
    (1, "Change a Setting"),
    (2, "Configure Advanced Sushi Arguments", lambda o: o.sync_workflow.get("enable_sushi_advanced_args")),
    (3, "Configure Audio Encode Settings", lambda o: o.merge_workflow.get("encode_lossless_audio_before_merging")),
    (4, "Restore Default Settings"),
    (5, "Clear Logs"),
    (6, "View Settings Help"),
    (7, "Return to Main Menu")
]


def _get_menu_options(settings_obj):
    """Return top-level settings menu options with visibility rules applied."""
    return [
        option[:2]
        for option in MENU_OPTIONS
        if len(option) == 2 or (len(option) == 3 and option[2](settings_obj))
    ]

SECTION_SUB_OPTIONS = [
    (1, Section.GEN.value),
    (2, Section.SYNC.value),
    (3, Section.MERGE_WRK.value),
    (4, Section.MERGE_SRC.value),
    (5, Section.MERGE_DST.value),
    (6, Section.MERGE_SUB.value),
    (7, GO_BACK_OPTION_LABEL)
]

def _get_formatted_value(value):
    """Return formatted value for table display"""
    match value:
        case True:
            return f"{cu.Fore.GREEN}Enabled{cu.style_reset}"
        case False:
            return f"{cu.Fore.RED}Disabled{cu.style_reset}"
        case QueueTheme():
            theme_name = QUEUE_THEMES.get(value, "Unknown")
            return f"{cu.Fore.MAGENTA}{theme_name}{cu.style_reset}"
        case AudioEncodeCodec():
            return f"{cu.Fore.MAGENTA}{value.value}{cu.style_reset}"
        case _:
            _color = cu.Fore.YELLOW if value else cu.Fore.LIGHTBLACK_EX
            _value = value if value else "Not set"
            return f"{_color}{_value}{cu.style_reset}"
        
def _get_settings_rows(obj):
    """Return the settings rows used by the table and selection flow."""
    rows = [
        # General Section
        {
            "section": Section.GEN,
            "label": "Queue Theme",
            "attr": "general.queue_theme",
            "value": obj.general.get("queue_theme"),
            "description": "Controls how queued jobs are displayed in the terminal queue view.",
            "show": True,
        },
        {
            "section": Section.GEN,
            "label": "Save Sushi sync logs",
            "attr": "general.save_sushi_logs",
            "value": obj.general.get("save_sushi_logs"),
            "description": "Saves detailed Sushi synchronization logs for each sync operation.",
            "show": True,
        },
        {
            "section": Section.GEN,
            "label": "Save Aegisub-CLI resample logs",
            "attr": "general.save_aegisub_resample_logs",
            "value": obj.general.get("save_aegisub_resample_logs"),
            "description": "Saves logs generated while resampling subtitles with Aegisub-CLI.",
            "show": True,
        },
        {
            "section": Section.GEN,
            "label": "Save MKVMerge logs",
            "attr": "general.save_mkvmerge_logs",
            "value": obj.general.get("save_mkvmerge_logs"),
            "divider": True,
            "description": "Saves MKVMerge execution logs during post-sync merge operations.",
            "show": True,
        },

        # Subtitle Sync Section
        {
            "section": Section.SYNC,
            "label": "Use high quality resampling (better sync accuracy)",
            "attr": "sync_workflow.use_high_quality_resample",
            "value": obj.sync_workflow.get("use_high_quality_resample"),
            "description": "Uses a higher quality audio resampling method that can improve sync accuracy.",
            "show": True,
        },
        {
            "section": Section.SYNC,
            "label": "Allow advanced Sushi arguments",
            "attr": "sync_workflow.enable_sushi_advanced_args",
            "value": obj.sync_workflow.get("enable_sushi_advanced_args"),
            "divider": True,
            "description": "Enables custom Sushi argument overrides for advanced synchronization tuning.",
            "show": True,
        },

        # Merge - Workflow Section
        {
            "section": Section.MERGE_WRK,
            "label": "Merge automatically on sync completion",
            "attr": "merge_workflow.merge_files_after_execution",
            "value": obj.merge_workflow.get("merge_files_after_execution"),
            "description": "Automatically starts file merge after a sync job finishes successfully.",
            "show": True,
        },
        {
            "section": Section.MERGE_WRK,
            "label": "Encode lossless audio before merging",
            "attr": "merge_workflow.encode_lossless_audio_before_merging",
            "value": obj.merge_workflow.get("encode_lossless_audio_before_merging"),
            "description": "Encodes extracted lossless tracks to a configured lossy codec before merging.",
            "show": True,
        },
        {
            "section": Section.MERGE_WRK,
            "label": "Encoding audio codec",
            "attr": "merge_workflow.encode_codec",
            "value": obj.merge_workflow.get("encode_codec"),
            "description": "Selects which audio codec is used when pre-merge audio encoding is enabled.",
            "show": obj.merge_workflow.get("encode_lossless_audio_before_merging"),
        },
        {
            "section": Section.MERGE_WRK,
            "label": "Resample synced sub before merge",
            "attr": "merge_workflow.resample_subs_on_merge",
            "value": obj.merge_workflow.get("resample_subs_on_merge"),
            "description": "Resamples the synced subtitle to match target video resolution before merging.",
            "show": True,
        },
        {
            "section": Section.MERGE_WRK,
            "label": "Delete generated audio/subtitle files after merge",
            "attr": "merge_workflow.delete_generated_files_after_merge",
            "value": obj.merge_workflow.get("delete_generated_files_after_merge"),
            "divider": True,
            "description": "Removes temporary generated subtitle/audio files after merge completes.",
            "show": True,
        },

        # Merge - Source File Section
        {
            "section": Section.MERGE_SRC,
            "label": "Copy attachments",
            "attr": "merge_src_file.copy_attachments",
            "value": obj.merge_src_file.get("copy_attachments"),
            "description": "Copies attachments from the source file into the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_SRC,
            "label": "Copy chapters",
            "attr": "merge_src_file.copy_chapters",
            "value": obj.merge_src_file.get("copy_chapters"),
            "description": "Copies chapter entries from the source file into the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_SRC,
            "label": "Copy global tags",
            "attr": "merge_src_file.copy_global_tags",
            "value": obj.merge_src_file.get("copy_global_tags"),
            "description": "Copies container-level tags from the source file into the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_SRC,
            "label": "Copy track tags",
            "attr": "merge_src_file.copy_track_tags",
            "value": obj.merge_src_file.get("copy_track_tags"),
            "divider": True,
            "description": "Copies per-track metadata tags from the source file into the merged output.",
            "show": True,
        },

        # Merge - Sync Target File Section
        {
            "section": Section.MERGE_DST,
            "label": "Copy only selected sync audio track",
            "attr": "merge_dst_file.copy_audio_tracks",
            "value": obj.merge_dst_file.get("copy_audio_tracks"),
            "description": "Includes only the selected target audio track used during synchronization.",
            "show": True,
        },
        {
            "section": Section.MERGE_DST,
            "label": "Copy attachments",
            "attr": "merge_dst_file.copy_attachments",
            "value": obj.merge_dst_file.get("copy_attachments"),
            "description": "Copies attachments from the target file into the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_DST,
            "label": "Copy chapters",
            "attr": "merge_dst_file.copy_chapters",
            "value": obj.merge_dst_file.get("copy_chapters"),
            "description": "Copies chapter entries from the target file into the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_DST,
            "label": "Copy subtitles",
            "attr": "merge_dst_file.copy_subtitle_tracks",
            "value": obj.merge_dst_file.get("copy_subtitle_tracks"),
            "description": "Copies subtitle tracks from the target file in addition to the synced subtitle.",
            "show": True,
        },
        {
            "section": Section.MERGE_DST,
            "label": "Copy global tags",
            "attr": "merge_dst_file.copy_global_tags",
            "value": obj.merge_dst_file.get("copy_global_tags"),
            "description": "Copies container-level tags from the target file into the merged output.",
            "show": True,
        },
        {
            "section": Section.MERGE_DST,
            "label": "Copy track tags",
            "attr": "merge_dst_file.copy_track_tags",
            "value": obj.merge_dst_file.get("copy_track_tags"),
            "divider": True,
            "description": "Copies per-track metadata tags from the target file into the merged output.",
            "show": True,
        },

        # Merge - Synced Subtitle Section
        {
            "section": Section.MERGE_SUB,
            "label": "Set default flag",
            "attr": "merge_synced_sub_file.default_flag",
            "value": obj.merge_synced_sub_file.get("default_flag"),
            "description": "Sets the merged synced subtitle track as default in the output file.",
            "show": True,
        },
        {
            "section": Section.MERGE_SUB,
            "label": "Set forced flag",
            "attr": "merge_synced_sub_file.forced_flag",
            "value": obj.merge_synced_sub_file.get("forced_flag"),
            "description": "Marks the merged synced subtitle track as forced in the output file.",
            "show": True,
        },
        {
            "section": Section.MERGE_SUB,
            "label": "Use custom track name",
            "attr": "merge_synced_sub_file.custom_trackname",
            "value": obj.merge_synced_sub_file.get("custom_trackname"),
            "description": "Enables a custom name for the merged synced subtitle track.",
            "show": True,
        },
        {
            "section": Section.MERGE_SUB,
            "label": "Default track name",
            "attr": "merge_synced_sub_file.trackname",
            "value": obj.merge_synced_sub_file.get("trackname"),
            "description": "Sets the subtitle track name used when custom track naming is enabled.",
            "show": obj.merge_synced_sub_file.get("custom_trackname"),
        },
    ]

    return list(filter(None, rows))

def _render_settings_table(rows):
    """Create and return settings table"""
    tb = PrettyTable(["Section", "Name", "Value"])
    
    for row in rows:
        tb.add_row(
            [row["section"].value, row["label"], 
            _get_formatted_value(row["value"])],
            divider=row.get("divider", False)
        )
    
    return tb

def _select_queue_theme():
    """Display queue theme options and update setting based on user selection"""
    go_back_id = len(QUEUE_THEMES) + 1
    options = [(idx, label) for idx, label in enumerate(QUEUE_THEMES.values(), 1)]
    options.append((go_back_id, GO_BACK_OPTION_LABEL))

    choice_idx = choice_prompt.get(options=options, nl_before=False, nl_after=False)
    if choice_idx == go_back_id:
        return None

    return next(theme for theme, label in QUEUE_THEMES.items() if label == options[choice_idx - 1][1])

def _select_audio_codec():
    """Display audio codec options and update setting based on user selection"""
    go_back_id = len(AudioEncodeCodec) + 1
    options = [(idx, codec.value) for idx, codec in enumerate(AudioEncodeCodec, 1)]
    options.append((go_back_id, GO_BACK_OPTION_LABEL))

    choice_idx = choice_prompt.get(options=options, nl_before=False, nl_after=False)
    if choice_idx == go_back_id:
        return None

    return next(codec for codec in AudioEncodeCodec if codec.value == options[choice_idx - 1][1])

def _update_value(obj, option):
    """Update value for selected option (handles both direct attributes and nested dict options)"""
    path = option.split(".")
    if len(path) == 1:
        curr_val = getattr(obj, option)
    else:
        parent_attr, dict_key = path[0], path[1]
        parent = getattr(obj, parent_attr)
        curr_val = parent.get(dict_key)
    
    new_val = None
    print(f"Current value: {_get_formatted_value(curr_val)}\n")
    
    match curr_val:
        case QueueTheme():
            new_val = _select_queue_theme()
        case AudioEncodeCodec():
            new_val = _select_audio_codec()
        case bool():
            prompt = "Disable" if curr_val else "Enable"
            if confirm_prompt.get(f"{prompt} option?"):
                new_val = not curr_val  
        case str():
            user_input = input_prompt.get(allow_empty=True)
            if confirm_prompt.get():
                new_val = user_input
                
    if new_val is not None:
        if len(path) == 1:
            setattr(obj, option, new_val)
        else:
            parent_attr, dict_key = path[0], path[1]
            parent = getattr(obj, parent_attr)
            parent[dict_key] = new_val
        obj.handle_save()

def _handle_option_choice(section_options):
    """Handle user choice for setting inside a section"""
    go_back_id = len(section_options) + 1
    options = section_options + [(go_back_id, GO_BACK_OPTION_LABEL)]

    selected_option_id = choice_prompt.get("Select setting to modify: ", options)
    if selected_option_id == go_back_id:
        return None # Go Back option selected at option level

    return next(idx for idx, _ in options if idx == selected_option_id)

def _select_setting_to_update(rows):
    """Prompt user to select a setting to update and return the corresponding attribute name"""
    while True:
        selected_section_idx = choice_prompt.get("Select section: ", options=SECTION_SUB_OPTIONS, nl_after=False)
        
        section_val = SECTION_SUB_OPTIONS[selected_section_idx - 1][1]
        if section_val == GO_BACK_OPTION_LABEL:
            return None # Go Back option selected at section level

        section_rows = [
            (idx, row["label"])
            for idx, row in enumerate(rows, 1)
            if row["section"].value == section_val
        ]
        
        selected_option = _handle_option_choice(section_rows)
        if selected_option:
           return rows[selected_option - 1]["attr"] # Return attribute name for selected setting

def _view_settings_help(visible_rows):
    cu.clear_screen()
    cu.print_header("Settings Help", nl_after=True)
    
    settings_by_section = {
        section: [row for row in visible_rows if row["section"] == section]
        for section in Section
    }

    for section, settings in settings_by_section.items():
        section_title = f" {section.value} "
        section_divider = "=" * max(8, 56 - len(section_title))
        print(f"{cu.Fore.LIGHTMAGENTA_EX}{section_divider}{section_title}{section_divider}{cu.style_reset}")
        for setting in settings:
            cu.print_help_text(setting["label"], setting["description"])
        print()
    input_prompt.get("Press Enter to close...  ", allow_empty=True, nl_before=True)
    

def show_settings_menu(settings_obj):
    """Display and handle options in new menu"""
    if not isinstance(settings_obj, Settings):
        cu.print_error("Invalid settings object provided.", False)
        return

    while True:
        cu.clear_screen()
        cu.print_header("App Settings\n")
        visible_rows = _get_settings_rows(settings_obj)
        tbl = _render_settings_table(visible_rows)
        print(tbl)

        menu_options = _get_menu_options(settings_obj)
        choice = choice_prompt.get(options=menu_options, nl_after=False)
        match choice:
            case 1:
                selected = _select_setting_to_update(visible_rows)
                if selected:
                    _update_value(settings_obj, selected)
            case 2:
                configure_advanced_sushi_args(settings_obj)
            case 3:
                current_codec = settings_obj.merge_workflow.get("encode_codec")
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