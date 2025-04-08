import sys
import weakref
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QMessageBox, QGraphicsColorizeEffect
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor


class DualLabelButton(QPushButton):
    """
    A QPushButton subclass that provides two distinct labels for its off and on states.

    Attributes:
        off_label (str): The label to display when the button is not checked.
        on_label (str): The label to display when the button is checked.
    """

    def __init__(self, off_label: str, on_label: str, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the DualLabelButton with off and on labels.
        """
        super().__init__(off_label, parent)
        self.off_label = off_label
        self.on_label = on_label
        self.setCheckable(True)


class WidgetButtonsRow(QWidget):
    """
    A widget that provides a vertical layout of multiple buttons for quick actions.
    This widget organizes both regular and checkable buttons in a vertical layout.
    """
    def __init__(self) -> None:
        """
        Initialize the WidgetButtonsRow with predefined buttons.
        """
        super().__init__()

        # Create regular (non-checkable) buttons.
        self.f1_button: QPushButton = QPushButton("F1. Fit Cole")
        self.f2_button: QPushButton = QPushButton("F2 Fit Bode")
        self.f3_button: QPushButton = QPushButton("F3 AllFreqs")
        self.f4_button: QPushButton = QPushButton("F4 Save plot")
        self.f5_button: QPushButton = QPushButton("F5 File Back")
        self.f6_button: QPushButton = QPushButton("F6 File Forth")
        self.f7_button: QPushButton = QPushButton("F7 Recover")
        self.f8_button: QPushButton = QPushButton("F8 Sliders Default")

        # Create checkable buttons using DualLabelButton.
        self.f9_button: DualLabelButton = DualLabelButton("F9 +Rinf", "F9 -Rinf")
        self.f10_button: DualLabelButton = DualLabelButton("F10 Parallel", "F10 Series")
        self.f11_button: DualLabelButton = DualLabelButton("F11 Tail Left", "F11 Tail Right")
        self.f12_button: DualLabelButton = DualLabelButton("F12 Damping", "F12 Constrains On")

        # Create additional regular buttons.
        self.fup_button: QPushButton = QPushButton("PageUp. Max Freq")
        self.fdown_button: QPushButton = QPushButton("PageDown. Min freq")

        # Group all buttons into a list for easy iteration.
        self._buttons_list = [
            self.f1_button, self.f2_button, self.f3_button,
            self.f4_button, self.f5_button, self.f6_button,
            self.f7_button, self.f8_button, self.f9_button,
            self.f10_button, self.f11_button, self.f12_button,
            self.fup_button, self.fdown_button
        ]

        self._setup_layout()
        self._setup_connections()

    def _setup_layout(self) -> None:
        """
        Set up the vertical layout for all buttons without spacing.
        """
        layout = QVBoxLayout()
        layout.setSpacing(0)  # Remove spacing between buttons
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins around the layout
        # Reduce button size
        
        button_height = 20  # Adjust height 25
        font_size = 9  # Adjust font size
        # Ensure buttons have no padding/margin and are tightly packed
        for button in self._buttons_list:
            button.setStyleSheet(f"font-size: {font_size}px; margin: 0; padding: 0;")  # Remove internal button spacing
            button.setFixedHeight(button_height)  # Ensures uniform height and no gaps
            layout.addWidget(button)
    
        widget_min_width = 30
        widget_max_width = 100
        self.setLayout(layout)
        self.setMaximumWidth(widget_max_width)
        self.setMinimumSize(widget_min_width, button_height * len(self._buttons_list))
        #self.setMinimumWidth(widget_min_width)
        #self.setMaximumWidth(widget_min_width)


    def _setup_connections(self) -> None:
        """
        Connect each button's signal to its appropriate slot.
        """
        # For each button, connect clicked signals for regular buttons and
        # toggled signals for checkable buttons.
        for btn in self._buttons_list:
            if not btn.isCheckable():
                btn.clicked.connect(self._on_regular_button_clicked)
            else:
                btn.toggled.connect(self._on_checkable_toggled)

    def _on_regular_button_clicked(self) -> None:
        """
        Handle clicks for non-checkable buttons.

        Briefly flashes the button green if the operation is successful;
        otherwise, displays an error message.
        """
        button = self.sender()
        if not isinstance(button, QPushButton):
            return

        # Replace the following with the actual logic to verify the operation.
        order_is_correct = True

        if order_is_correct:
            self._flash_button_green(button, duration=1500)
        else:
            QMessageBox.warning(self, "Error", "Order not correctly executed!")

    def _on_checkable_toggled(self, state: bool) -> None:
        """
        Handle toggling of checkable buttons.

        Updates the button's text and style based on its state.

        Args:
            state (bool): The new state of the button (True for checked, False for unchecked).
        """
        button = self.sender()
        if not isinstance(button, QPushButton):
            return

        if state:
            # Set the button text to its "on" label and apply a red background.
            button.setText(button.on_label)  # type: ignore[attr-defined]
            button.setStyleSheet("QPushButton { background-color: red; }")
        else:
            # Revert the button text to its "off" label and remove the background.
            button.setText(button.off_label)  # type: ignore[attr-defined]
            button.setStyleSheet("QPushButton { background-color: none; }")

    def _flash_button_green(self, button: QPushButton, duration: int = 1500) -> None:
        """
        Briefly flash the button green for a specified duration.

        Args:
            button (QPushButton): The button to flash.
            duration (int): Duration in milliseconds for the flash effect.
        """
        effect = QGraphicsColorizeEffect()
        effect.setColor(QColor(0, 150, 0, 255))
        effect.setStrength(1.0)
        button.setGraphicsEffect(effect)

        # Use a weak reference to the button to prevent issues if the button is deleted.
        weak_button = weakref.ref(button)
        QTimer.singleShot(
            duration, lambda: weak_button() and weak_button().setGraphicsEffect(None)
        )


if __name__ == "__main__":
    # Quick test for the WidgetButtonsRow.
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = WidgetButtonsRow()
    widget.setWindowTitle("Test WidgetButtonsRow")
    widget.show()
    sys.exit(app.exec_())

