from prettytable import PrettyTable

from .prompts import choice_prompt, confirm_prompt, input_prompt

from ..models.settings import Settings

from ..utils import console_utils as cu
from ..utils import file_utils as fu
from ..models.enums import Section, QueueTheme

GO_BACK_OPTION_LABEL = "Go Back"

QUEUE_THEMES = {
    QueueTheme.CLASSIC: "Classic",
    QueueTheme.CARD: "Card",
    QueueTheme.YAML: "YAML-inspired"
}

MENU_OPTIONS = [
    (1, "Change a Setting"),
    (2, "Restore Default Settings"),
    (3, "Clear Logs"),
    (4, "Return to Main Menu")
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
        case _:
            _color = cu.Fore.YELLOW if value else cu.Fore.LIGHTBLACK_EX
            _value = value if value else "Not set"
            return f"{_color}{_value}{cu.style_reset}"
        
def _get_settings_rows(obj):
    """Return the settings rows used by the table and selection flow."""
    divider_flag = True

    rows = [
        # General Section
        (Section.GEN, "Queue Theme", "queue_theme", obj.queue_theme),
        (Section.GEN, "Save Sushi sync logs", "save_sushi_logs", obj.save_sushi_logs),
        (Section.GEN, "Save Aegisub-CLI resample logs", "save_aegisub_resample_logs", obj.save_aegisub_resample_logs),
        (Section.GEN, "Save MKVMerge logs", "save_mkvmerge_logs", obj.save_mkvmerge_logs, divider_flag),

        # Subtitle Sync Section
        (Section.SYNC, "Use high quality resampling (better sync accuracy)", "use_high_quality_resample", obj.use_high_quality_resample, divider_flag),
        
        # Merge - Workflow Section
        (Section.MERGE_WRK, "Merge automatically on sync completion", "merge_files_after_execution", obj.merge_files_after_execution),
        (Section.MERGE_WRK, "Resample synced sub before merge", "resample_subs_on_merge", obj.resample_subs_on_merge),
        (Section.MERGE_WRK, "Delete generated subtitle files after merge", "delete_generated_files_after_merge", obj.delete_generated_files_after_merge, divider_flag),

        # Merge - Source File Section
        (Section.MERGE_SRC, "Copy attachments", "src_copy_attachments", obj.src_copy_attachments),
        (Section.MERGE_SRC, "Copy chapters", "src_copy_chapters", obj.src_copy_chapters),
        (Section.MERGE_SRC, "Copy global tags", "src_copy_global_tags", obj.src_copy_global_tags),
        (Section.MERGE_SRC, "Copy track tags", "src_copy_track_tags", obj.src_copy_track_tags, divider_flag),
        
        # Merge - Sync Target File Section
        (Section.MERGE_DST, "Copy only selected sync audio track", "dst_copy_audio_tracks", obj.dst_copy_audio_tracks),
        (Section.MERGE_DST, "Copy attachments", "dst_copy_attachments", obj.dst_copy_attachments),
        (Section.MERGE_DST, "Copy chapters", "dst_copy_chapters", obj.dst_copy_chapters),
        (Section.MERGE_DST, "Copy subtitles", "dst_copy_subtitle_tracks", obj.dst_copy_subtitle_tracks),
        (Section.MERGE_DST, "Copy global tags", "dst_copy_global_tags", obj.dst_copy_global_tags),
        (Section.MERGE_DST, "Copy track tags", "dst_copy_track_tags", obj.dst_copy_track_tags, divider_flag),
        
        # Merge - Synced Subtitle Section
        (Section.MERGE_SUB, "Set default flag", "sub_default_flag", obj.sub_default_flag),
        (Section.MERGE_SUB, "Set forced flag", "sub_forced_flag", obj.sub_forced_flag),
        (Section.MERGE_SUB, "Use custom track name", "sub_custom_trackname", obj.sub_custom_trackname),
    ]

    if obj.sub_custom_trackname:
        rows.append((Section.MERGE_SUB, "Default track name", "sub_trackname", obj.sub_trackname))

    return rows

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

def _update_value(obj, option):
    """Update value for selected option"""
    curr_val = getattr(obj, option)
    new_val = None
    
    print(f"Current value: {_get_formatted_value(curr_val)}\n")
    
    match curr_val:
        case QueueTheme():
            new_val = _select_queue_theme()
        case bool():
            prompt = "Disable" if curr_val else "Enable"
            if confirm_prompt.get(f"{prompt} option?"):
                new_val = not curr_val  
        case str():
            user_input = input_prompt.get(allow_empty=True)
            if confirm_prompt.get():
                new_val = user_input
                
    if new_val is not None:       
        setattr(obj, option, new_val)
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

        choice = choice_prompt.get(options=MENU_OPTIONS, nl_after=False)
        match choice:
            case 1:
                selected = _select_setting_to_update(table_rows)
                if selected:
                    _update_value(settings_obj, selected)
            case 2 if confirm_prompt.get():
                settings_obj.restore()
                cu.print_success("Settings restored to default values.")
            case 3:
                if confirm_prompt.get("Are you sure you want to clear the logs? This action cannot be undone.", nl_before=True, destructive=True):
                    fu.clear_logs(settings_obj.data_path)
                    cu.print_success("Logs cleared.")
                    break
            case _:
                break