from prettytable import PrettyTable

from .prompts import choice_prompt, confirm_prompt, input_prompt
from .sushi_advanced_args_menu import configure_advanced_sushi_args
from.codec_bitrates_config_menu import configure_audio_encode_bitrates

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
    (3, "Configure Audio Encoding Bitrates", lambda o: o.merge_workflow.get("encode_lossless_audio_before_merging")),
    (4, "Restore Default Settings"),
    (5, "Clear Logs"),
    (6, "Return to Main Menu")
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
    divider_flag = True

    rows = filter(None, [
        # General Section
        (Section.GEN, "Queue Theme", "general.queue_theme", obj.general.get("queue_theme")),
        (Section.GEN, "Save Sushi sync logs", "general.save_sushi_logs", obj.general.get("save_sushi_logs")),
        (Section.GEN, "Save Aegisub-CLI resample logs", "general.save_aegisub_resample_logs", obj.general.get("save_aegisub_resample_logs")),
        (Section.GEN, "Save MKVMerge logs", "general.save_mkvmerge_logs", obj.general.get("save_mkvmerge_logs"), divider_flag),

        # Subtitle Sync Section
        (Section.SYNC, "Use high quality resampling (better sync accuracy)", "sync_workflow.use_high_quality_resample", obj.sync_workflow.get("use_high_quality_resample")),
        (Section.SYNC, "Allow advanced Sushi arguments", "sync_workflow.enable_sushi_advanced_args", obj.sync_workflow.get("enable_sushi_advanced_args"), divider_flag),
        
        # Merge - Workflow Section
        (Section.MERGE_WRK, "Merge automatically on sync completion", "merge_workflow.merge_files_after_execution", obj.merge_workflow.get("merge_files_after_execution")),
        (Section.MERGE_WRK, "Encode lossless audio before merging", "merge_workflow.encode_lossless_audio_before_merging", obj.merge_workflow.get("encode_lossless_audio_before_merging")),
        (Section.MERGE_WRK, "Encoding audio codec", "merge_workflow.encode_ffmpeg_codec", obj.merge_workflow.get("encode_ffmpeg_codec")) if obj.merge_workflow.get("encode_lossless_audio_before_merging") else None,
        (Section.MERGE_WRK, "Resample synced sub before merge", "merge_workflow.resample_subs_on_merge", obj.merge_workflow.get("resample_subs_on_merge")),
        (Section.MERGE_WRK, "Delete generated subtitle files after merge", "merge_workflow.delete_generated_files_after_merge", obj.merge_workflow.get("delete_generated_files_after_merge"), divider_flag),

        # Merge - Source File Section
        (Section.MERGE_SRC, "Copy attachments", "merge_src_file.copy_attachments", obj.merge_src_file.get("copy_attachments")),
        (Section.MERGE_SRC, "Copy chapters", "merge_src_file.copy_chapters", obj.merge_src_file.get("copy_chapters")),
        (Section.MERGE_SRC, "Copy global tags", "merge_src_file.copy_global_tags", obj.merge_src_file.get("copy_global_tags")),
        (Section.MERGE_SRC, "Copy track tags", "merge_src_file.copy_track_tags", obj.merge_src_file.get("copy_track_tags"), divider_flag),
        
        # Merge - Sync Target File Section
        (Section.MERGE_DST, "Copy only selected sync audio track", "merge_dst_file.copy_audio_tracks", obj.merge_dst_file.get("copy_audio_tracks")),
        (Section.MERGE_DST, "Copy attachments", "merge_dst_file.copy_attachments", obj.merge_dst_file.get("copy_attachments")),
        (Section.MERGE_DST, "Copy chapters", "merge_dst_file.copy_chapters", obj.merge_dst_file.get("copy_chapters")),
        (Section.MERGE_DST, "Copy subtitles", "merge_dst_file.copy_subtitle_tracks", obj.merge_dst_file.get("copy_subtitle_tracks")),
        (Section.MERGE_DST, "Copy global tags", "merge_dst_file.copy_global_tags", obj.merge_dst_file.get("copy_global_tags")),
        (Section.MERGE_DST, "Copy track tags", "merge_dst_file.copy_track_tags", obj.merge_dst_file.get("copy_track_tags"), divider_flag),
        
        # Merge - Synced Subtitle Section
        (Section.MERGE_SUB, "Set default flag", "merge_synced_sub_file.default_flag", obj.merge_synced_sub_file.get("default_flag")),
        (Section.MERGE_SUB, "Set forced flag", "merge_synced_sub_file.forced_flag", obj.merge_synced_sub_file.get("forced_flag")),
        (Section.MERGE_SUB, "Use custom track name", "merge_synced_sub_file.custom_trackname", obj.merge_synced_sub_file.get("custom_trackname")),
        (Section.MERGE_SUB, "Default track name", "merge_synced_sub_file.trackname", obj.merge_synced_sub_file.get("trackname")) if obj.merge_synced_sub_file.get("custom_trackname") else None
    ])

    return list(rows)

def _generate_settings_table(rows):
    """Create and return settings table"""
    tb = PrettyTable(["Section", "Name", "Value"])
    
    for row in rows:
        section, option, _, value = row[:4]
        has_divider = len(row) > 4 and row[4]
        tb.add_row([section.value, option, _get_formatted_value(value)], divider=has_divider)
    
    tb.add_autoindex("Option")
    
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
        obj._save()

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
            (idx, row[1])
            for idx, row in enumerate(rows, 1)
            if row[0].value == section_val
        ]
        
        selected_option = _handle_option_choice(section_rows)
        if selected_option:
           return rows[selected_option - 1][2] # Return attribute name for selected setting
    

def show_settings_menu(settings_obj):
    """Display and handle options in new menu"""
    if not isinstance(settings_obj, Settings):
        cu.print_error("Invalid settings object provided.", False)
        return

    while True:
        cu.clear_screen()
        cu.print_header("App Settings\n")
        table_rows = _get_settings_rows(settings_obj)
        tbl = _generate_settings_table(table_rows)
        print(tbl)

        menu_options = _get_menu_options(settings_obj)
        choice = choice_prompt.get(options=menu_options, nl_after=False)
        match choice:
            case 1:
                selected = _select_setting_to_update(table_rows)
                if selected:
                    _update_value(settings_obj, selected)
            case 2:
                configure_advanced_sushi_args(settings_obj)
            case 3:
                configure_audio_encode_bitrates(settings_obj)
            case 4:
                if confirm_prompt.get():
                    settings_obj.restore()
                    cu.print_success("Settings restored to default values.")
            case 5:
                if confirm_prompt.get("Are you sure you want to clear the logs? This action cannot be undone.", nl_before=True, destructive=True):
                    fu.clear_logs(settings_obj.data_path)
                    cu.print_success("Logs cleared.")
                    break
            case _:
                break