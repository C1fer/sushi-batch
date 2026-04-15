import sys

from PyQt6.QtWidgets import QApplication, QFileDialog


class FileDialog:
    # Set as class attribute to avoid creating multiple QApplication instances
    app = QApplication(sys.argv)

    @staticmethod
    def askfilenames(title, filetypes):
        """Open a dialog to select multiple files and return the selected file paths."""
        ftypes = ";;".join(filetypes)
        selected_files, _ = QFileDialog.getOpenFileNames(caption=title, filter=ftypes, options=QFileDialog.Option.ReadOnly)
        return selected_files

    @staticmethod
    def askdirectory(title):
        """Open a dialog to select a directory and return the selected path."""
        return QFileDialog.getExistingDirectory(caption=title)
