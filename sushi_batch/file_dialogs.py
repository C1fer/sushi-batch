import sys

from PyQt6.QtWidgets import QApplication, QFileDialog


class FileDialog:
    # Set as class attribute to avoid creating multiple QApplication instances
    app = QApplication(sys.argv)

    # Set filetypes for File Select dialogs
    @staticmethod
    def set_filter(filetypes):
        return ";;".join(filetypes)

    # File select Dialog
    @staticmethod
    def askfilenames(title, filetypes):
        ftypes = FileDialog.set_filter(filetypes)
        selected_files, _ = QFileDialog.getOpenFileNames(caption=title, filter=ftypes, options=QFileDialog.Option.ReadOnly)
        return selected_files

    # Directory Select Dialog
    @staticmethod
    def askdirectory(title):
        return QFileDialog.getExistingDirectory(caption=title)
