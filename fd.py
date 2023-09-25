import sys
from PyQt5.QtWidgets import QApplication, QFileDialog

app = QApplication(sys.argv)

options = QFileDialog.Options()
options |= QFileDialog.ReadOnly

file_dialog = QFileDialog()
file_paths, _ = file_dialog.getOpenFileNames(None, 'Open Files', '', 'Text Files (*.txt);;All Files (*)', options=options)
file_dialog.getd
if file_paths:
    for file_path in file_paths:
        print(f'Selected file: {file_path}')
else:
    print('No files selected.')

app.exec_()
