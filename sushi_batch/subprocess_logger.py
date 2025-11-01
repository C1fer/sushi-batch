from datetime import datetime
from os import makedirs, path

from . import settings 

class SubProcessLogger:
    @staticmethod
    def set_log_path(src_file, dir_name):
        output_dirpath = path.join(settings.config.data_path, dir_name)
        makedirs(output_dirpath, exist_ok=True)

        base_name = path.basename(src_file)
        name, _ = path.splitext(base_name)

        current_datetime = datetime.now().strftime("%Y-%m-%d - %H.%M.%S")

        return path.join(output_dirpath, f"{current_datetime} - {name}.log")

    @staticmethod
    def save_log_output(log_path, content):
        try:
            with open(log_path, "w", encoding="utf-8") as log_file:
                log_file.write(content)
        except Exception as e:
            print(f"Error saving log file {log_path}: {e}")