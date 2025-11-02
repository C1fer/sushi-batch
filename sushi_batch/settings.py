import json
from os import makedirs, path

from prettytable import PrettyTable

from . import console_utils as cu
from .enums import Section


class Settings():

    def __init__(self):
        # Default paths
        self.data_path = path.join(path.expanduser('~/Documents'), 'SushiBatchTool')
        self.file_path = path.join(self.data_path, "settings.json")

        # General settings
        self.merge_files_after_execution = True
        self.resample_subs_on_merge = False
        self.save_sushi_logs = True
        self.save_aegisub_resample_logs = False
        self.save_mkvmerge_logs = False
        
        # Source file settings
        self.src_copy_attachments = True
        self.src_copy_chapters = False
        self.src_copy_global_tags = False
        self.src_copy_track_tags = False

        # Destination file settings
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
        """_Save settings to JSON file"""
        with open(self.file_path, "w", encoding="utf-8") as settings_file:
            json.dump(self.__dict__, settings_file, indent=4)

    def _load(self):
        """Load settings from JSON file"""
        with open(self.file_path, "r", encoding="utf-8") as settings_file:
            data = json.load(settings_file)
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

    def _get_formated_value(self, value):
        """Return formatted value for table display"""
        match value:
            case True:
                return f"{cu.Fore.GREEN}Enabled{cu.style_reset}"
            case False:
                return f"{cu.Fore.RED}Disabled{cu.style_reset}"
            case _:
                return f"{cu.Fore.YELLOW}{value}{cu.style_reset}"
            
    def _generate_settings_table(self):
        """Create and return settings table"""
        tb = PrettyTable(["Section", "Name", "Value"])
        
        rows = [
            # General Section
            (Section.GEN, "Merge synced sub automatically", self.merge_files_after_execution),
            (Section.GEN, "Resample synced sub resolution before merging", self.resample_subs_on_merge),
            (Section.GEN, "Save Sushi logs", self.save_sushi_logs),
            (Section.GEN, "Save Aegisub-CLI resample logs", self.save_aegisub_resample_logs),
            (Section.GEN, "Save MKVMerge logs", self.save_mkvmerge_logs, True),

            # Source File Section
            (Section.SRC, "Copy attachments", self.src_copy_attachments),
            (Section.SRC, "Copy chapters", self.src_copy_chapters),
            (Section.SRC, "Copy global tags", self.src_copy_global_tags),
            (Section.SRC, "Copy track tags", self.src_copy_track_tags, True),
            
            # Destination File Section
            (Section.DST, "Only copy audio track used for sync", self.dst_copy_audio_tracks),
            (Section.DST, "Copy attachments", self.dst_copy_attachments),
            (Section.DST, "Copy chapters", self.dst_copy_chapters),
            (Section.DST, "Copy subtitles", self.dst_copy_subtitle_tracks),
            (Section.DST, "Copy global tags", self.dst_copy_global_tags),
            (Section.DST, "Copy track tags", self.dst_copy_track_tags, True),
            
            # Synced Subtitle Section
            (Section.SUB, "Set default flag", self.sub_default_flag),
            (Section.SUB, "Set forced flag", self.sub_forced_flag),
            (Section.SUB, "Use custom track name", self.sub_custom_trackname),
        ]
        
        if self.sub_custom_trackname:
            rows.append((Section.SUB, "Default track name", self.sub_trackname))
        
        for row in rows:
            section, option, value = row[:3]
            has_divider = len(row) > 3 and row[3]
            tb.add_row([section.value, option, self._get_formated_value(value)], divider=has_divider)
        
        tb.add_autoindex("Option")
        
        return tb

    def handle_options(self):
        """Display and handle options in new menu"""
        options = {
            "1" : "Change option value",
            "2" : "Restore default settings",
            "3" : "Return to main menu"
        }

        while True:
            cu.clear_screen()
            cu.print_header("App Settings\n")
            tbl = self._generate_settings_table()
            print(tbl)
            cu.show_menu_options(options)

            choice = cu.get_choice(1,3)
            match choice:
                case 1:
                    opt, opt_label = self.select_option(tbl.rows)
                    self.update_value(opt, opt_label)
                case 2 if cu.confirm_action():
                    self.restore()
                case 3:
                    break
    
    def update_value(self, option, option_label):
        """Update value for selected option"""
        curr_val = getattr(self, option)
        new_val = None
        
        print(f"Option: {cu.fore.YELLOW}{option_label}")
        print(f"\nCurrent value: {self._get_formated_value(curr_val)}\n")
        
        match curr_val:
            case bool():
                prompt = "Disable" if curr_val else "Enable"
                if cu.confirm_action(f"{prompt} option? (Y/N): "):
                    new_val = not curr_val  
            case str():
                user_input = input("New value: ")
                if cu.confirm_action():
                    new_val = user_input
                    
        if new_val is not None:       
            setattr(self, option, new_val)
            self._save()
    
    def select_option(self, rows):
        """Display options and get user selection"""
        idx = cu.get_choice(1, len(rows), "Select option to modify: ")
    
        _, sel_option_label = rows[idx - 1][:2]
    
        attr_names = list(self.__dict__)[2:]  # Exclude data_path and file_path
        sel_option = attr_names[idx - 1]
        
        return sel_option, sel_option_label
    
    def restore(self):
        """Restore default settings"""
        self.__init__()
        self._save()
        

# Create Settings instance to allow access in other modules
config = Settings()