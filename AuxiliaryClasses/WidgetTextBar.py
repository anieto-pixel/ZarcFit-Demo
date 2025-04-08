
"""
Created on Tue Jan  7 11:37:36 2025

@author: agarcian
"""

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow, QSlider,
                             QWidget, QVBoxLayout, QTextEdit)

class WidgetTextBar(QWidget):
    """A widget that displays key/value pairs with colored labels."""

    def __init__(self, keys_1=None):
        """
        Initialize the WidgetTextBar.
        Parameters: keys_1 (list): A list of keys with the values to be displayed labels.
        """
        super().__init__()
        self.default_text = "default"
        self.value_labels = {}  # Maps keys to QLabel instances.
        self.key_colors = {}    # Maps keys to HTML colors for label text.
        
        self._user_comment= self.default_text

        keys_1 = keys_1 or []  # Ensure it's a list

        # Sort and order the keys by type/colour
        ordered_keys = self._sort_keys_by_suffix(keys_1)

        # Initialize labels and layout
        self._build_ui(ordered_keys)
        
    #--------------------------------------
    #   Public Methods
    #--------------------------------------- 
    def get_comment(self):
        return {'comment':self._user_comment}
    
    def clear_text_box(self):  # <-- NEW PUBLIC METHOD
        """
        Clears the text input box and resets the stored comment.
        """
        self._comment_edit.clear()
        self._user_comment = self.default_text
    
    
    #--------------------------------------
    #   Private Methods
    #---------------------------------------
    def _sort_keys_by_suffix(self, keys):
        """
        Sorts and categorizes keys based on their suffix.

        Returns:
            list: Ordered list of keys for display.
        """
        categorized_keys = {"h": [], "m": [], "l": [], "other": []}

        for key in keys:
            suffix = key[-1] if key[-1] in categorized_keys else "other"
            categorized_keys[suffix].append(key)

        # Sort within each category and return merged ordered keys
        return (
            sorted(categorized_keys["h"]) +
            sorted(categorized_keys["m"]) +
            sorted(categorized_keys["l"]) +
            sorted(categorized_keys["other"])
        )

    def _assign_color_by_suffix(self, key):
        """
        Assigns colors based on the key suffix.
        """
        return {"h": "red", "m": "green", "l": "blue"}.get(key[-1], "black")

    
    def _build_ui(self, ordered_keys):
        """
        Creates labels with the correct order and formatting.
        """
        main_layout = QHBoxLayout()
        
        #Layout for displayed text labels
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(10)

        # Setting diplayed text labels
        for key in ordered_keys:
            color = self._assign_color_by_suffix(key)
            self.key_colors[key] = color

            initial_text = f"<b><font color='{color}'>{key}:</font></b> 0.000000"
            value_label = QLabel(initial_text)
            value_label.setAlignment(Qt.AlignLeft)
            #arbitrary_space_per_element=130
            arbitrary_space_per_element=85
            value_label.setFixedWidth(arbitrary_space_per_element + len(key))

            h_layout.addWidget(value_label)
            self.value_labels[key] = value_label
        h_layout.addStretch()
        
        #window to write on
        # Now create a QTextEdit on the right
        self._comment_edit = QTextEdit()
        self._comment_edit.setFixedHeight(25)
        self._comment_edit.setPlaceholderText("Type your comment here...")
        self._comment_edit.textChanged.connect(self._on_text_changed)
        
        # Put them together in a main horizontal layout
        main_layout.addLayout(h_layout)       # The row of keys on the left
        main_layout.addWidget(self._comment_edit)  # The text box on the right
        
        
        self.setLayout(main_layout)
        self.setFixedHeight(self.sizeHint().height())
        
    def _update_text(self, dictionary):
        """
        Updates the text of labels based on the provided dictionary.

        The key text remains colored, while the value text is displayed in black.
        """
        for key, value in dictionary.items():
            label = self.value_labels.get(key)
            if label:
                color = self.key_colors[key]
                label.setText(f"<b><font color='{color}'>{key}:</font></b> {value:.3g}")
#            else:
#                print(f"WidgetTextBar Warning: Key '{key}' is not configured. Add it in config.ini")
                
    def _on_text_changed(self):
        """
        Callback whenever the user modifies the text in `_comment_edit`.
        We store it in `self.user_comment`.
        """
        self._user_comment = self._comment_edit.toPlainText()


#########################
# Manual Testing
#########################

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Dictionary 1 has keys ending with h, m, l (red, green, blue).
    dic_1 = {"pQh": 2.0067, "pQm": 0.00008, "pQl": 20.450004, "pS": 999.0}

    # Dictionary 2 has keys that do not follow the h/m/l suffix convention.
    dic_2 = {"unknown": 0.0067}

    # Merge dictionaries for updating.
    dic_3 = dic_1 | dic_2

    # Create main window.
    window = QMainWindow()

    # Create the WidgetTextBar with keys from both dictionaries.
    text_bar = WidgetTextBar(dic_1.keys() | dic_2.keys())
    text_bar._update_text(dic_3)

    # Create a central widget and layout to hold the text bar and sliders.
    central_widget = QWidget()
    central_layout = QVBoxLayout()
    central_layout.addWidget(text_bar)

    # For each key, create a label and a corresponding horizontal slider.
    sliders = {}
    for key, value in dic_3.items():
        lbl = QLabel(key)
        central_layout.addWidget(lbl)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(-1000000)
        slider.setMaximum(1000000)
        slider.setValue(int(value * 10))
        # Update the dictionary and text bar when the slider value changes.
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
