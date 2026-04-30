from datetime import datetime
from os import makedirs, path

from ..models import settings 

from importlib.metadata import version

class ExecutionLogger:
    internal_log_indicator = "[Sushi-Batch] "
    log_header = f"{internal_log_indicator}Running with version {version('sushi-batch')}\n\n"
    
    @staticmethod
    def set_log_path(src_file, dir_name):
        """Create a log file path to write into a specified directory."""
        output_dirpath = path.join(settings.config.data_path, dir_name)
        makedirs(output_dirpath, exist_ok=True)

        base_name = path.basename(src_file)
        name, _ = path.splitext(base_name)

        current_datetime = datetime.now().strftime("%Y-%m-%d - %H.%M.%S")

        return path.join(output_dirpath, f"{current_datetime} - {name}.log")

    @classmethod
    def _get_section_log_content(cls, section_name=None, section_indicator=None):
        if section_name:
            if not section_indicator:
                section_indicator = "=" * 15
            return f"{section_indicator}{section_name}{section_indicator}\n"
        return ""

    @classmethod
    def save_log_output(cls, log_path, content, section_name=None, section_indicator=None, is_internal=False):
        """Save content to log file. section_indicator and section_name can be provided to add a section header to the content."""
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                _header = cls.log_header if log_file.tell() == 0 else ""
                _internal_log_indicator = cls.internal_log_indicator if is_internal else ""
                _section_header = cls._get_section_log_content(section_name, section_indicator)
                
                log_file.write(_header + _section_header + _internal_log_indicator + content + "\n\n")
        except Exception as e:
            print(f"Error saving log file at {log_path}: {e}")