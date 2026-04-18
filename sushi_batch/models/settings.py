import json
from os import makedirs, path

from prettytable import PrettyTable

from ..utils import console_utils as cu
from ..utils.json_utils import SettingsDecoder, SettingsEncoder
from ..utils.prompts import choice_prompt, confirm_prompt, input_prompt

from .enums import Section, QueueTheme

QUEUE_THEMES = {
    QueueTheme.CLASSIC: "Classic",
    QueueTheme.CARD: "Card",
    QueueTheme.YAML: "YAML-inspired"
}

MENU_OPTIONS = [
    (1, "Change option value"),
    (2, "Restore default settings"),
    (3, "Return to main menu")
]

SETTING_SECTION_OPTIONS = [
    (1, Section.GEN.value),
    (2, Section.WORKFLOW.value),
    (3, Section.MERGE_SRC.value),
    (4, Section.MERGE_DST.value),
    (5, Section.MERGE_SUB.value)
]

class Settings():

    def __init__(self):
        # Default paths
        self.data_path = path.join(path.expanduser('~/Documents'), 'SushiBatchTool')
        self.file_path = path.join(self.data_path, "settings.json")

        # General settings
        self.queue_theme = QueueTheme.CARD
        self.save_sushi_logs = True
        self.save_aegisub_resample_logs = False
        self.save_mkvmerge_logs = False

        # Workflow Settings
        self.merge_files_after_execution = True
        self.resample_subs_on_merge = False
        self.delete_generated_files_after_merge = False
        
        # Source file settings
        self.src_copy_attachments = True
        self.src_copy_chapters = False
        self.src_copy_global_tags = False
        self.src_copy_track_tags = False

        # Sync target file settings
        self.dst_copy_audio_tracks = False
        self.dst_copy_attachments = True
        self.dst_copy_chapters = True
        self.dst_copy_subtitle_tracks = True
        self.dst_copy_global_tags = True
        self.dst_copy_track_tags = True

        # Subtitle settings
        self.sub_default_flag = True
        self.sub_forced_flag = False
        self.sub_custom_trackname = False
        self.sub_trackname = "Synced Sub"

    def _save(self):
        """Save settings to JSON file"""
        try: 
            converted_json = json.dumps(self, indent=4, cls=SettingsEncoder)
            with open(self.file_path, "w", encoding="utf-8") as settings_file:
                settings_file.write(converted_json)
        except Exception as e:
            cu.print_error(f"Error saving settings: {e}", True)

    def _load(self):
        """Load settings from JSON file"""
        with open(self.file_path, "r", encoding="utf-8") as settings_file:
            data = json.load(settings_file, cls=SettingsDecoder)
        # Update instance attributes with loaded settings
        for key, value in data.items():
                setattr(self, key, value)
    
    def handle_load(self):
        """Load settings from file or create new file with default settings"""
        if path.exists(self.file_path):
            self._load()
        else:
            makedirs(self.data_path, exist_ok=True)
            self._save()

    def _get_formatted_value(self, value):
        """Return formatted value for table display"""
        match value:
            case True:
                return f"{cu.Fore.GREEN}Enabled{cu.style_reset}"
            case False:
                return f"{cu.Fore.RED}Disabled{cu.style_reset}"
            case QueueTheme():
                theme_name = QUEUE_THEMES.get(value, "Unknown")
                return f"{cu.Fore.CYAN}{theme_name}{cu.style_reset}"
            case _:
                return f"{cu.Fore.YELLOW}{value}{cu.style_reset}"
            
    def _generate_settings_table(self):
        """Create and return settings table"""
        tb = PrettyTable(["Section", "Name", "Value"])
        DIVIDER_FLAG = True
        
        rows = [
            # General Section
            (Section.GEN, "Queue Theme", self.queue_theme),
            (Section.GEN, "Save Sushi sync logs", self.save_sushi_logs),
            (Section.GEN, "Save Aegisub-CLI resample logs", self.save_aegisub_resample_logs),
            (Section.GEN, "Save MKVMerge logs", self.save_mkvmerge_logs, DIVIDER_FLAG),

            # Workflow Section
            (Section.WORKFLOW, "Merge automatically on sync completion", self.merge_files_after_execution),
            (Section.WORKFLOW, "Resample synced sub before merge", self.resample_subs_on_merge),
            (Section.WORKFLOW, "Delete generated subtitle files after merge", self.delete_generated_files_after_merge, DIVIDER_FLAG),

            # Source File Section
            (Section.MERGE_SRC, "Copy attachments", self.src_copy_attachments),
            (Section.MERGE_SRC, "Copy chapters", self.src_copy_chapters),
            (Section.MERGE_SRC, "Copy global tags", self.src_copy_global_tags),
            (Section.MERGE_SRC, "Copy track tags", self.src_copy_track_tags, DIVIDER_FLAG),
            
            # Sync Target File Section
            (Section.MERGE_DST, "Copy only selected sync audio track", self.dst_copy_audio_tracks),
            (Section.MERGE_DST, "Copy attachments", self.dst_copy_attachments),
            (Section.MERGE_DST, "Copy chapters", self.dst_copy_chapters),
            (Section.MERGE_DST, "Copy subtitles", self.dst_copy_subtitle_tracks),
            (Section.MERGE_DST, "Copy global tags", self.dst_copy_global_tags),
            (Section.MERGE_DST, "Copy track tags", self.dst_copy_track_tags, DIVIDER_FLAG),
            
            # Synced Subtitle Section
            (Section.MERGE_SUB, "Set default flag", self.sub_default_flag),
            (Section.MERGE_SUB, "Set forced flag", self.sub_forced_flag),
            (Section.MERGE_SUB, "Use custom track name", self.sub_custom_trackname),
        ]
        
        if self.sub_custom_trackname:
            rows.append((Section.MERGE_SUB, "Default track name", self.sub_trackname))
        
        for row in rows:
            section, option, value = row[:3]
            has_divider = len(row) > 3 and row[3]
            tb.add_row([section.value, option, self._get_formatted_value(value)], divider=has_divider)
        
        tb.add_autoindex("Option")
        
        return tb

    def handle_menu_options(self):
        """Display and handle options in new menu"""
        while True:
            cu.clear_screen()
            cu.print_header("App Settings\n")
            tbl = self._generate_settings_table()
            print(tbl)

            choice = choice_prompt.get(options=MENU_OPTIONS)
            match choice:
                case 1:
                    selected = self.select_setting_to_update(tbl.rows)
                    self.update_value(selected)
                case 2 if confirm_prompt.get():
                    self.restore()
                case 3:
                    break

    def select_queue_theme(self):
        """Display queue theme options and update setting based on user selection"""
        options = [(idx, theme_label) for idx, theme_label in enumerate(QUEUE_THEMES.values(), 1)]
        choice = choice_prompt.get(options=options, nl_before=False)
        

        return list(QUEUE_THEMES.keys())[choice - 1]  # Map selected index back to QueueTheme enum

    def update_value(self, option):
        """Update value for selected option"""
        curr_val = getattr(self, option)
        new_val = None
        
        print(f"\nCurrent value: {self._get_formatted_value(curr_val)}\n")
        
        match curr_val:
            case QueueTheme():
                new_val = self.select_queue_theme()
            case bool():
                prompt = "Disable" if curr_val else "Enable"
                if confirm_prompt.get(f"{prompt} option?"):
                    new_val = not curr_val  
            case str():
                user_input = input_prompt.get(allow_empty=True)
                if confirm_prompt.get():
                    new_val = user_input
                    
        if new_val is not None:       
            setattr(self, option, new_val)
            self._save()
    
    def select_setting_to_update(self, rows):
        """Prompt user to select a setting to update and return the corresponding attribute name"""
        selected_section_idx = choice_prompt.get("Select section: ", SETTING_SECTION_OPTIONS)
        section_val = SETTING_SECTION_OPTIONS[selected_section_idx - 1][1]
        section_rows = [
            (idx, row[2])
            for idx, row
            in enumerate(rows, 1)
            if row[1] == section_val
        ]

        selected_option_id = choice_prompt.get("Select setting to modify: ", section_rows)
    
        attr_names = list(self.__dict__)[2:]  # Exclude data_path and file_path
        return attr_names[selected_option_id - 1]
        
    def restore(self):
        """Restore default settings"""
        self.__init__()
        self._save()
        

# Create Settings instance to allow access in other modules
config = Settings()