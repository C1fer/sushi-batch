from PyQt6.QtCore import QCoreApplication
import sys
from collections.abc import Sequence

from PyQt6.QtWidgets import QApplication, QFileDialog, QWidget


class FileDialog:
    """Wrapper around Qt dialogs used by the TUI flows."""
    app: QApplication | None = None

    @classmethod
    def _ensure_app(cls) -> QApplication:
        """Create a QApplication only when needed and reuse existing one."""
        existing: QCoreApplication | None = QApplication.instance()
        if isinstance(existing, QApplication):
            cls.app: QApplication = existing
            return existing

        cls.app = QApplication(sys.argv)
        cls.app.setQuitOnLastWindowClosed(False)
        return cls.app

    @staticmethod
    def _build_filter(filetypes: Sequence[str] | str) -> str:
        if isinstance(filetypes, str):
            return filetypes
        return ";;".join(filetypes)

    @classmethod
    def askfilenames(cls, title: str, filetypes: Sequence[str] | str, initial_dir: str = "", parent: QWidget | None = None) -> list[str]:
        """Open a dialog to select multiple files and return selected paths."""
        cls._ensure_app()
        selected_files, _ = QFileDialog.getOpenFileNames(
            parent=parent,
            caption=title,
            directory=initial_dir,
            filter=cls._build_filter(filetypes),
            options=QFileDialog.Option.ReadOnly,
        )
        return selected_files

    @classmethod
    def askdirectory(cls, title: str, initial_dir: str = "", parent: QWidget | None = None) -> str:
        """Open a dialog to select a directory and return selected path."""
        cls._ensure_app()
        return QFileDialog.getExistingDirectory(parent=parent, caption=title, directory=initial_dir)
