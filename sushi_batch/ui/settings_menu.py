from prettytable import PrettyTable

from ..models.settings import Settings

from ..utils import console_utils as cu
from ..utils.prompts import choice_prompt, confirm_prompt, input_prompt

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
    (3, "Return to Main Menu")
]

SECTION_SUB_OPTIONS = [
    (1, Section.GEN.value),
    (2, Section.WORKFLOW.value),
    (3, Section.MERGE_SRC.value),
    (4, Section.MERGE_DST.value),
    (5, Section.MERGE_SUB.value),
    (6, GO_BACK_OPTION_LABEL)
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
        
def _generate_settings_table(obj):
    """Create and return settings table"""
    tb = PrettyTable(["Section", "Name", "Value"])
    DIVIDER_FLAG = True
    
    rows = [
        # General Section
        (Section.GEN, "Queue Theme", obj.queue_theme),
        (Section.GEN, "Save Sushi sync logs", obj.save_sushi_logs),
        (Section.GEN, "Save Aegisub-CLI resample logs", obj.save_aegisub_resample_logs),
        (Section.GEN, "Save MKVMerge logs", obj.save_mkvmerge_logs, DIVIDER_FLAG),

        # Workflow Section
        (Section.WORKFLOW, "Merge automatically on sync completion", obj.merge_files_after_execution),
        (Section.WORKFLOW, "Resample synced sub before merge", obj.resample_subs_on_merge),
        (Section.WORKFLOW, "Delete generated subtitle files after merge", obj.delete_generated_files_after_merge, DIVIDER_FLAG),

        # Source File Section
        (Section.MERGE_SRC, "Copy attachments", obj.src_copy_attachments),
        (Section.MERGE_SRC, "Copy chapters", obj.src_copy_chapters),
        (Section.MERGE_SRC, "Copy global tags", obj.src_copy_global_tags),
        (Section.MERGE_SRC, "Copy track tags", obj.src_copy_track_tags, DIVIDER_FLAG),
        
        # Sync Target File Section
        (Section.MERGE_DST, "Copy only selected sync audio track", obj.dst_copy_audio_tracks),
        (Section.MERGE_DST, "Copy attachments", obj.dst_copy_attachments),
        (Section.MERGE_DST, "Copy chapters", obj.dst_copy_chapters),
        (Section.MERGE_DST, "Copy subtitles", obj.dst_copy_subtitle_tracks),
        (Section.MERGE_DST, "Copy global tags", obj.dst_copy_global_tags),
        (Section.MERGE_DST, "Copy track tags", obj.dst_copy_track_tags, DIVIDER_FLAG),
        
        # Synced Subtitle Section
        (Section.MERGE_SUB, "Set default flag", obj.sub_default_flag),
        (Section.MERGE_SUB, "Set forced flag", obj.sub_forced_flag),
        (Section.MERGE_SUB, "Use custom track name", obj.sub_custom_trackname),
    ]
    
    if obj.sub_custom_trackname:
        rows.append((Section.MERGE_SUB, "Default track name", obj.sub_trackname))
    
    for row in rows:
        section, option, value = row[:3]
        has_divider = len(row) > 3 and row[3]
        tb.add_row([section.value, option, _get_formatted_value(value)], divider=has_divider)
    
    tb.add_autoindex("Option")
    
    return tb

def _select_queue_theme():
    """Display queue theme options and update setting based on user selection"""
    theme_mapping = {idx: name for idx, (_, name) in enumerate(QUEUE_THEMES.items(), 1)}
    options = [(idx, name) for idx, name in theme_mapping.items()]
    options.append((len(theme_mapping) + 1, GO_BACK_OPTION_LABEL))

    choice_idx = choice_prompt.get(options=options, nl_before=False, nl_after=False)    
    if choice_idx == len(options):
        return None

    return theme_mapping.get(choice_idx)

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

def _handle_option_choice(obj, section_options):
    """Handle user choice for setting inside a section"""
    option_count = len(section_options)
    section_options.append((option_count + 1, GO_BACK_OPTION_LABEL))

    selected_option_id = choice_prompt.get("Select setting to modify: ", section_options)
    if selected_option_id == option_count + 1:
        return None # Go Back option selected at option level

    attr_names = list(obj.__dict__)[2:]  # Exclude data_path and file_path
    return attr_names[selected_option_id - 1]

def _select_setting_to_update(obj, rows):
    """Prompt user to select a setting to update and return the corresponding attribute name"""
    while True:
        selected_section_idx = choice_prompt.get("Select section: ", options=SECTION_SUB_OPTIONS, nl_after=False)
        
        section_val = SECTION_SUB_OPTIONS[selected_section_idx - 1][1]
        if section_val == GO_BACK_OPTION_LABEL:
            return None # Go Back option selected at section level

        section_rows = [
            (idx, row[2])
            for idx, row in enumerate(rows, 1)
            if row[1] == section_val
        ]
        selected_option = _handle_option_choice(obj, section_rows)
        if selected_option:
            return selected_option
    

def show_settings_menu(settings_obj):
    """Display and handle options in new menu"""
    if not isinstance(settings_obj, Settings):
        cu.print_error("Invalid settings object provided.", False)
        return

    while True:
        cu.clear_screen()
        cu.print_header("App Settings\n")
        tbl = _generate_settings_table(settings_obj)
        print(tbl)

        choice = choice_prompt.get(options=MENU_OPTIONS, nl_after=False)
        match choice:
            case 1:
                selected = _select_setting_to_update(settings_obj, tbl.rows)
                if selected:
                    _update_value(settings_obj, selected)
            case 2 if confirm_prompt.get():
                settings_obj.restore()
                cu.print_success("Settings restored to default values.")
            case 3:
                break