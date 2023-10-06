import sys

from PyQt6.QtWidgets import QApplication, QFileDialog


class FileDialog:
    # Set as class attribute to avoid creating multiple QApplication instances
    app = QApplication(sys.argv)

    # Set filetypes for File Select dialogs
    @staticmethod
    def set_filter(filetypes):
        formatted_filter = ""
        for ft in filetypes:
            if ft == filetypes[-1]:
                formatted_filter += ft
            else:
                formatted_filter += f"{ft};;"
        return formatted_filter

    # File select Dialog
    @staticmethod
    def askfilenames(title, filetypes):
        ftypes = FileDialog.set_filter(filetypes)
        selected_files, _ = QFileDialog.getOpenFileNames(caption=title, filter=ftypes, options=QFileDialog.Option.ReadOnly)
        return selected_files
        sys.exit(app.exec())

    # Directory Select Dialog
    @staticmethod
    def askdirectory(title):
        selected_dir = QFileDialog.getExistingDirectory(caption=title)
        return selected_dir
        sys.exit(app.exec())
