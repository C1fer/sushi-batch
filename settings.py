from os import path, makedirs
import json
from prettytable import PrettyTable
from enums import Section
import console_utils as cu


class Settings():

    def __init__(self):
        # Default path
        self.data_path = path.join(path.expanduser('~/Documents'), 'SushiBatchTool')
        self.file_path = path.join(self.data_path, "settings.json")

        # General settings
        self.merge_files_after_execution = True
        self.save_sushi_logs = True
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


    # Save settings to JSON file
    def save(self):
        with open(self.file_path, "w", encoding="utf-8") as settings_file:
            json.dump(self.__dict__, settings_file, indent=4)


    # Load settings from JSON file
    def load(self):
        with open(self.file_path, "r", encoding="utf-8") as settings_file:
            data = json.load(settings_file)
            # Update instance attributes with loaded settings
            for key, value in data.items():
                setattr(self, key, value)
    
    # Settings load handler
    def handle_load(self):
        if path.exists(self.file_path):
            self.load()
        else:
            makedirs(self.data_path, exist_ok=True)
            self.save()

    # Set format for Value row
    def set_value_format(self, value):
        match value:
            case True:
                return f"{cu.Fore.GREEN}Enabled{cu.style_reset}"
            case False:
                return f"{cu.Fore.RED}Disabled{cu.style_reset}"
            case _:
                return f"{cu.Fore.YELLOW}{value}{cu.style_reset}"
            
    # Show Settings inside a table
    def set_table(self):
        # Initialize table with columns
        tb = PrettyTable(["Section", "Option", "Value"])
        
        # General Section 
        tb.add_rows(
            [
                [Section.GEN.value, "Merge synced sub automatically", self.set_value_format(self.merge_files_after_execution)], 
                [Section.GEN.value, "Save Sushi logs", self.set_value_format(self.save_sushi_logs)]  
            ]
        )
        tb.add_row([Section.GEN.value, "Save MKVMerge logs", self.set_value_format(self.save_mkvmerge_logs)], divider=True)

       
        # Source File Section 
        tb.add_rows(
            [
                [Section.SRC.value, "Copy attachments", self.set_value_format(self.src_copy_attachments)],
                [Section.SRC.value, "Copy chapters", self.set_value_format(self.src_copy_chapters)],
                [Section.SRC.value, "Copy global tags", self.set_value_format(self.src_copy_global_tags)],
            ]
        )
        tb.add_row([Section.SRC.value, "Copy track tags", self.set_value_format(self.src_copy_track_tags)], divider=True)
        
        # Destination File Section
        tb.add_rows(
            [
                [Section.DST.value, "Only copy audio track used for sync", self.set_value_format(self.dst_copy_audio_tracks)],
                [Section.DST.value, "Copy attachments", self.set_value_format(self.dst_copy_attachments)],
                [Section.DST.value, "Copy chapters", self.set_value_format(self.dst_copy_chapters)],
                [Section.DST.value, "Copy subtitles", self.set_value_format(self.dst_copy_subtitle_tracks)],
                [Section.DST.value, "Copy global tags", self.set_value_format(self.dst_copy_global_tags)],
            ]
        )
        tb.add_row([Section.DST.value, "Copy track tags", self.set_value_format(self.dst_copy_track_tags)], divider=True)

        # Synced Subtitle Section 
        tb.add_rows(
            [
                [Section.SUB.value, "Set default flag", self.set_value_format(self.sub_default_flag)],
                [Section.SUB.value, "Set forced flag", self.set_value_format(self.sub_forced_flag)],
                [Section.SUB.value, "Use custom track name", self.set_value_format(self.sub_custom_trackname)],
            ]
        )
        
        if self.sub_custom_trackname:
            tb.add_row([Section.SUB.value, "Default track name", self.set_value_format(self.sub_trackname)])

        # Add auto index column to the left of the table
        tb.add_autoindex("Index")

        return tb

    # Settings menu handler
    def handle_options(self):
        options = {
            "1" : "Change option value",
            "2" : "Restore default settings",
            "3" : "Return to main menu"
        }

        while True:
            # Show table and menu options
            cu.clear_screen()
            cu.print_header("App Settings\n")
            tbl = self.set_table()
            print(tbl)
            cu.show_menu_options(options)

            choice = cu.get_choice(1,3)
            match choice:
                case 1:
                    opt, opt_label = self.select_option(tbl.rows)
                    self.update_value(opt, opt_label)
                case 2:
                    if cu.confirm_action():
                        self.restore()
                case 3:
                    break
    
    # Update value for selected option
    def update_value(self, option, option_label):
        # Get current option value
        curr_val = getattr(self, option)
        new_val = None
        
        print(f"Option: {cu.fore.YELLOW}{option_label}")
        print(f"\nCurrent value: {self.set_value_format(curr_val)}\n")
        
        match curr_val:
            case bool():
                prompt = "Disable" if curr_val else "Enable"
                if cu.confirm_action(f"{prompt} option? (Y/N): "):
                    new_val = not curr_val  # If Y, toggle setting   
            case str():
                user_input = input("New value: ")
                if cu.confirm_action():
                    new_val = user_input
                    
        if new_val is not None:       
            # Update value and save changes
            setattr(self, option, new_val)
            self.save()
    
    # Select option from table    
    def select_option(self, rows):
        # Get user input
        idx = cu.get_choice(1, len(rows), "Select an index: ")
        
        # Get selected option attr name and row label
        attr_names = list(self.__dict__)
        sel_option = attr_names[idx+1]
        sel_option_label = rows[idx-1][2]
        
        return sel_option, sel_option_label
    
    # Restore default settings    
    def restore(self):
        default_settings = Settings()
        self.__dict__.update(default_settings.__dict__)
        del default_settings
        self.save()
        

# Create Settings instance to allow access in other modules
config = Settings()