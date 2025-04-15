import os
import csv

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QFileDialog, QHBoxLayout, QMessageBox, QVBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal

def get_dpi_scale():
    """
    Returns a scaling factor based on a 96 DPI baseline.
    """
    screen = QApplication.primaryScreen()
    if screen:
        return 96.0 / screen.logicalDotsPerInch()
    return 1.0

class ErrorWindow:
    """
    Provides a static method to display critical error messages in a dialog box.
    """
    @staticmethod
    def show_error_message(message, title="Error"):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()

class FileWriter:
    """
    Handles writing rows of data to CSV files safely.
    """
    @staticmethod
    def write_to_file(file_path, rows, header=None):
        if not file_path:
            ErrorWindow.show_error_message("FileWriter.write_to_file: No file selected for writing.")
            return
        try:
            with open(file_path, "a", newline="") as f:
                writer = csv.writer(f)
                # Header ignored for backward compatibility.
                if isinstance(rows[0], (int, float, str)):
                    writer.writerow(rows)
                else:
                    for row in rows:
                        writer.writerow(row)
        except Exception as e:
            ErrorWindow.show_error_message(f"Could not write to file: {e}")

class FileSelector:
    """
    Handles file creation, selection, and validation.
    """
    @staticmethod
    def create_new_file(desired_type, set_file_callback, set_message_callback):
        file_path, _ = QFileDialog.getSaveFileName(
            None,
            f"Create New {desired_type} File",
            os.getcwd(),
            "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            if not file_path.lower().endswith(desired_type):
                file_path += desired_type
            if not os.path.exists(file_path):
                try:
                    with open(file_path, "w", newline="") as f:
                        pass  # Create empty file.
                    set_file_callback(file_path)
                except IOError as e:
                    ErrorWindow.show_error_message(f"Failed to create file: {str(e)}")
            else:
                set_message_callback("File already exists")
        else:
            set_message_callback("No file selected")

    @staticmethod
    def open_file_dialog(search_parameters, validate_callback, set_file_callback, set_message_callback):
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select File",
            os.getcwd(),
            search_parameters
        )
        if file_path:
            try:
                if validate_callback(file_path):
                    set_file_callback(file_path)
            except ValueError as e:
                ErrorWindow.show_error_message(str(e))
        else:
            set_message_callback("No file selected")

    @staticmethod
    def validate(file_path, desired_type):
        if not file_path.lower().endswith(desired_type):
            raise ValueError(f"The selected file must end with '{desired_type}'")
        return True

class WidgetOutputFile(QWidget):
    """
    A widget for creating or selecting a .csv output file and writing data to it.
    """
    output_file_selected = pyqtSignal(str)

    def __init__(self, variables_to_print=None, output_file=None):
        super().__init__()

        if variables_to_print is None:
            variables_to_print = []

        self.variables_to_print = variables_to_print
        self._desired_type = ".csv"
        self._search_parameters = "CSV Files (*.csv);;All Files (*)"
        self._output_file = output_file

        # Create UI elements.
        self._newfile_button = QPushButton("New File")
        self._select_button = QPushButton("Select .csv File")
        self._file_label = QLabel("No output file selected")

        self._initialize_ui()
        self._connect_signals()
        self._set_output_file(output_file)

    # Public Methods
    def get_output_file(self):
        return self._output_file

    def set_current_file(self, output_file):
        self._set_output_file(output_file)

    def print_variables_list(self):
        if not self._output_file:
            ErrorWindow.show_error_message("No output file selected. Please select or create a file first.")
            return
        if self.variables_to_print:
            FileWriter.write_to_file(
                file_path=self._output_file,
                rows=self.variables_to_print
            )

    def write_to_file(self, dictionary):
        if not self._output_file:
            ErrorWindow.show_error_message("No output file selected. Please select or create a file first.")
            return
        if not isinstance(dictionary, dict):
            ErrorWindow.show_error_message("write_to_file requires a dictionary. Received something else.")
            return
        row = [dictionary.get(key, "") for key in self.variables_to_print]
        FileWriter.write_to_file(
            file_path=self._output_file,
            rows=row,
            header=None
        )

    def find_row_in_file(self, head):
        try:
            with open(self._output_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in reversed(lines):
                columns = line.strip().split(",")
                if columns and columns[0] == head:
                    dictionary = dict(zip(self.variables_to_print, columns))
                    return dictionary
            return None
        except Exception as e:
            ErrorWindow.show_error_message(f"WidgetOutputFile.find_row_in_file: Error reading file: {e}")
            return None

    # Private Methods
    def _initialize_ui(self):
        scale = get_dpi_scale()
        layout = QHBoxLayout()
        # Use dynamic margins/spacing.
        margin = int(5 * scale)
        spacing = int(1 * scale)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)

        standard_size = (65, 15)  # Base size at 100% DPI (change these values if needed)
        new_width, new_height = standard_size
        self._select_button.setFixedSize(new_width, new_height)  # Modify to change button size
        self._newfile_button.setFixedSize(new_width, new_height)   # Modify to change button size

        font = self._select_button.font()
        font.setPointSize(7)  # modify to set font size 
        self._select_button.setFont(font)  
        self._newfile_button.setFont(font)  
        
        label_font = self._file_label.font()         
        label_font.setPointSize(7)                    
        self._file_label.setFont(label_font)           

        self._file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self._newfile_button)
        layout.addWidget(self._select_button)
        layout.addWidget(self._file_label)
        self.setLayout(layout)

    def _connect_signals(self):
        self._newfile_button.clicked.connect(self._handle_create_new_file)
        self._select_button.clicked.connect(self._handle_open_file_dialog)

    def _handle_create_new_file(self):
        FileSelector.create_new_file(
            self._desired_type,
            self._set_output_file,
            self._set_file_message
        )
        if self.variables_to_print:
            self.print_variables_list()

    def _handle_open_file_dialog(self):
        FileSelector.open_file_dialog(
            self._search_parameters,
            lambda path: FileSelector.validate(path, self._desired_type),
            self._set_output_file,
            self._set_file_message
        )

    def _set_output_file(self, file_path):
        if not isinstance(file_path, str):
            return
        self._output_file = file_path
        self._file_label.setText(os.path.basename(file_path))
        self.output_file_selected.emit(self._output_file)

    def _set_file_message(self, message):
        self._file_label.setText(message)

# -----------------------------------------------------------------------
# Test for WidgetOutputFile
# -----------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

    app = QApplication(sys.argv)
    vars_to_print = ["A", "B", "C", "D", "E"]
    widget = WidgetOutputFile(variables_to_print=vars_to_print)
    widget.setWindowTitle("WidgetOutputFile - Dictionary Test")
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(widget)
    write_test_button = QPushButton("Write Test Dictionary")
    layout.addWidget(write_test_button)
    container.setLayout(layout)
    container.show()

    def on_write_test_button():
        data_dict = {"A": 100, "C": 300, "Z": 999}
        widget.write_to_file(data_dict)

    write_test_button.clicked.connect(on_write_test_button)
    QTimer.singleShot(1000, lambda: widget.write_to_file({"A": 42}))
    sys.exit(app.exec_())







