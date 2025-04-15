import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QSlider,
    QWidget, QVBoxLayout, QTextEdit
)
from PyQt5.QtGui import QFontMetrics

def get_dpi_scale():
    """
    Compute a scaling factor based on a baseline of 96 DPI.
    For example, at 150% (≈144 DPI) the scale factor is ~0.67.
    """
    screen = QApplication.primaryScreen()
    if screen:
        return 96.0 / screen.logicalDotsPerInch()
    return 1.0

class WidgetTextBar(QWidget):
    """A widget that displays key/value pairs with colored labels."""
    def __init__(self, keys_1=None):
        """
        Initialize the WidgetTextBar.

        Parameters:
            keys_1 (list): A list of keys whose values will be displayed.
        """
        super().__init__()
        self.default_text = "default"
        self.value_labels = {}  # Maps keys to QLabel instances.
        self.key_colors = {}    # Maps keys to HTML colors for label text.
        self._user_comment = self.default_text

        # Use provided keys or an empty list.
        keys_1 = keys_1 or []

        # Sort keys by type/colour.
        ordered_keys = self._sort_keys_by_suffix(keys_1)

        # Build the UI using the ordered keys.
        self._build_ui(ordered_keys)

    #--------------------------------------
    #   Public Methods
    #-------------------------------------- 
    def get_comment(self):
        return {'comment': self._user_comment}
    
    def clear_text_box(self):
        """Clears the text input box and resets the stored comment."""
        self._comment_edit.clear()
        self._user_comment = self.default_text
    
    #--------------------------------------
    #   Private Methods
    #--------------------------------------
    def _sort_keys_by_suffix(self, keys):
        """
        Sorts keys based on their suffix.

        Returns:
            list: Ordered list of keys for display.
        """
        categorized_keys = {"h": [], "m": [], "l": [], "other": []}

        for key in keys:
            suffix = key[-1] if key[-1] in categorized_keys else "other"
            categorized_keys[suffix].append(key)

        # Sort within each category and return a merged list.
        return (
            sorted(categorized_keys["h"]) +
            sorted(categorized_keys["m"]) +
            sorted(categorized_keys["l"]) +
            sorted(categorized_keys["other"])
        )

    def _assign_color_by_suffix(self, key):
        """
        Returns the color based on the key suffix.
        """
        return {"h": "red", "m": "green", "l": "blue"}.get(key[-1], "black")

    def _build_ui(self, ordered_keys):
        scale = get_dpi_scale()
        main_layout = QHBoxLayout()
        # Remove all margins and spacing from the main layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Horizontal layout for the labels.
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(int(10 * scale))
    
        # Set up displayed labels.
        for key in ordered_keys:
            color = self._assign_color_by_suffix(key)
            self.key_colors[key] = color
            # Use a smaller font size for the key (9 * scale).
            initial_text = (
                f"<b><span style='font-size:{int(9 * scale)}px; color:{color};'>{key}:</span></b> 0.000000"
            )
            value_label = QLabel(initial_text)
            value_label.setAlignment(Qt.AlignLeft)
            # Set the label width based on DPI scaling; adjust as needed.
            arbitrary_space_per_element = int(85 * scale)
            value_label.setFixedWidth(arbitrary_space_per_element + len(key))
            h_layout.addWidget(value_label)
            self.value_labels[key] = value_label
    
        # Remove the stretch if you want the layout to end immediately after the labels.
        # h_layout.addStretch()  <-- Removed for a tight fit.
    
        # Create a text-edit area for user comments.
        self._comment_edit = QTextEdit()
        self._comment_edit.setFixedHeight(int(20 * scale))
        self._comment_edit.setPlaceholderText("Type your comment here...")
        self._comment_edit.setStyleSheet(f"font-size: {int(8 * scale)}px;")
        self._comment_edit.textChanged.connect(self._on_text_changed)
        
        # Combine the labels and the comment box in the main layout.
        main_layout.addLayout(h_layout)
        main_layout.addWidget(self._comment_edit)
        
        self.setLayout(main_layout)
        # Set the widget's height to its size hint.
        self.setFixedHeight(self.sizeHint().height())

    def _update_text(self, dictionary):
        """
        Updates label text based on the provided dictionary.
        """
        scale = get_dpi_scale()
        for key, value in dictionary.items():
            label = self.value_labels.get(key)
            if label:
                color = self.key_colors[key]
                # Use a smaller font size for the key (9 * scale).
                label.setText(
                    f"<b><span style='font-size:{int(9 * scale)}px; color:{color};'>{key}:</span></b> {value:.3g}"
                )

    def _on_text_changed(self):
        """Callback invoked when the text edit content changes."""
        self._user_comment = self._comment_edit.toPlainText()


#########################
# Manual Testing
#########################
if __name__ == "__main__":
    from PyQt5.QtWidgets import QMainWindow
    app = QApplication(sys.argv)

    # Example dictionaries.
    dic_1 = {"pQh": 2.0067, "pQm": 0.00008, "pQl": 20.450004, "pS": 999.0}
    dic_2 = {"unknown": 0.0067}
    dic_3 = dic_1 | dic_2

    # Create a main window.
    window = QMainWindow()

    # Create the WidgetTextBar using keys from both dictionaries.
    text_bar = WidgetTextBar(dic_1.keys() | dic_2.keys())
    text_bar._update_text(dic_3)

    # Create a central widget and layout.
    central_widget = QWidget()
    central_layout = QVBoxLayout()
    central_layout.addWidget(text_bar)

    # For each key, create a label and corresponding horizontal slider.
    sliders = {}
    for key, value in dic_3.items():
        lbl = QLabel(key)
        central_layout.addWidget(lbl)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(-1000000)
        slider.setMaximum(1000000)
        slider.setValue(int(value * 10))
        slider.valueChanged.connect(
            lambda val, k=key: (
                dic_3.update({k: val / 100.0}),
                text_bar._update_text(dic_3)
            )
        )
        sliders[key] = slider
        central_layout.addWidget(slider)

    central_widget.setLayout(central_layout)
    window.setCentralWidget(central_widget)
    window.setWindowTitle("Testing WidgetTextBar with Sliders")
    window.show()

    sys.exit(app.exec_())
