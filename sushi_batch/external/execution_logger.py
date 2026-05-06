from datetime import datetime
from importlib.metadata import version
from io import TextIOWrapper
from pathlib import Path

from ..models import settings

class ExecutionLogger:
    internal_log_indicator = "[Sushi-Batch] "
    log_header = f"{internal_log_indicator}Running with version {version('sushi-batch')}\n\n"
    
    @staticmethod
    def set_log_path(src_file: str, dir_name: str) -> str:
        """Create a log file path to write into a specified directory. Return the path to the log file."""
        current_datetime: str = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        output_dirpath: Path = Path(settings.config.data_path) / dir_name
        output_dirpath.mkdir(parents=True, exist_ok=True)
        name: str = Path(src_file).stem

        return str(output_dirpath / f"{current_datetime} - {name}.log")

    @classmethod
    def _get_section_log_content(cls, section_name: str | None = None, section_indicator: str | None = None) -> str:
        if section_name:
            if not section_indicator:
                section_indicator = "=" * 15
            return f"{section_indicator}{section_name}{section_indicator}\n"
        return ""

    @classmethod
    def save_log_output(cls, log_path: str, content: str, section_name: str | None = None, section_indicator: str | None = None, is_internal: bool = False) -> None:
        """Save content to log file. section_indicator and section_name can be provided to add a section header to the content."""
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                _header = cls.log_header if log_file.tell() == 0 else ""
                _internal_log_indicator = cls.internal_log_indicator if is_internal else ""
                _section_header = cls._get_section_log_content(section_name, section_indicator)
                
                log_file.write(_header + _section_header + _internal_log_indicator + content + "\n\n")
        except Exception as e:
            print(f"An error occurred while saving log file at {log_path}: {e}")
            

    @classmethod
    def save_log_output_to_fd(cls, file_descriptor: TextIOWrapper, content: str, section_name: str | None = None, section_indicator: str | None = None, is_internal: bool = False) -> None:
        """Save content to file descriptor. section_indicator and section_name can be provided to add a section header to the content."""
        try:
            _header = cls.log_header if file_descriptor.tell() == 0 else ""
            _internal_log_indicator = cls.internal_log_indicator if is_internal else ""
            _section_header = cls._get_section_log_content(section_name, section_indicator)
                
            file_descriptor.write(_header + _section_header + _internal_log_indicator + content + "\n\n")
            file_descriptor.flush()
        except Exception as e:
            print(f"An error occurred while saving log file to file descriptor: {e}")