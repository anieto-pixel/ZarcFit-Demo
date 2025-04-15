import sys
import weakref
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QMessageBox, QGraphicsColorizeEffect, QHBoxLayout
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor

def get_dpi_scale():
    """
    Compute a scaling factor based on a baseline of 96 DPI.
    """
    from PyQt5.QtWidgets import QApplication
    screen = QApplication.primaryScreen()
    if screen:
        return 96.0 / screen.logicalDotsPerInch()
    return 1.0

class DualLabelButton(QPushButton):
    """
    A QPushButton subclass that provides two distinct labels for its off and on states.
    """
    def __init__(self, off_label: str, on_label: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(off_label, parent)
        self.off_label = off_label
        self.on_label = on_label
        self.setCheckable(True)

class WidgetButtonsRow(QWidget):
    """
    A widget that provides a vertical layout of multiple buttons for quick actions.
    The widget is designed to have a minimum height about 1/3 of the screen,
    while the buttons themselves are scaled down at higher DPI to avoid excessive height.
    """
    def __init__(self) -> None:
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
        Set up the vertical layout for all buttons without spacing,
        and adjust button size using DPI-aware scaling.
        """
        scale = get_dpi_scale()
        layout = QVBoxLayout()
        layout.setSpacing(0)   # Remove spacing between buttons
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins around the layout

        # Base values defined at 100%.
        base_button_height = 20  # Base height at 100%
        base_font_size = 8       # Base font size at 100%
        
        # Compute scaled button height.
        button_height = int(base_button_height * scale)
        
        # Compute the scaled font size.
        # For high DPI (scale < 0.8, roughly 150%), reduce the computed font size further.
        if scale < 0.8:
            adjusted_font_size = int(base_font_size * scale * 0.9)
        else:
            adjusted_font_size = int(base_font_size * scale)

        # Set each button's style and fixed height.
        for button in self._buttons_list:
            button.setStyleSheet(
                f"font-size: {adjusted_font_size}px; margin: 0; padding: 0;"
            )
            button.setFixedHeight(button_height)
            layout.addWidget(button)

        widget_min_width = 30
        widget_max_width = 100
        self.setLayout(layout)
        self.setMaximumWidth(widget_max_width)

        # Instead of basing the minimum height solely on button heights,
        # base it on one-third of the available screen height.
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            screen_height = screen.availableGeometry().height()
            min_height = screen_height // 3
        else:
            min_height = button_height * len(self._buttons_list)

        self.setMinimumSize(widget_min_width, min_height)

    def _setup_connections(self) -> None:
        """
        Connect each button's signal to its appropriate slot.
        """
        for btn in self._buttons_list:
            if not btn.isCheckable():
                btn.clicked.connect(self._on_regular_button_clicked)
            else:
                btn.toggled.connect(self._on_checkable_toggled)

    def _on_regular_button_clicked(self) -> None:
        """
        Handle clicks for non-checkable buttons: flash green if successful or show an error.
        """
        button = self.sender()
        if not isinstance(button, QPushButton):
            return

        order_is_correct = True  # Replace with actual operation logic

        if order_is_correct:
            self._flash_button_green(button, duration=1500)
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Order not correctly executed!")

    def _on_checkable_toggled(self, state: bool) -> None:
        """
        Handle toggling of checkable buttons: update text and style based on state.
        """
        button = self.sender()
        if not isinstance(button, QPushButton):
            return

        if state:
            button.setText(button.on_label)  # type: ignore[attr-defined]
            button.setStyleSheet("QPushButton { background-color: red; }")
        else:
            button.setText(button.off_label)  # type: ignore[attr-defined]
            button.setStyleSheet("QPushButton { background-color: none; }")

    def _flash_button_green(self, button: QPushButton, duration: int = 1500) -> None:
        """
        Briefly flash the button green for the specified duration.
        """
        from PyQt5.QtWidgets import QGraphicsColorizeEffect
        effect = QGraphicsColorizeEffect()
        effect.setColor(QColor(0, 150, 0, 255))
        effect.setStrength(1.0)
        button.setGraphicsEffect(effect)

        weak_button = weakref.ref(button)
        QTimer.singleShot(
            duration, lambda: weak_button() and weak_button().setGraphicsEffect(None)
        )

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = WidgetButtonsRow()
    widget.setWindowTitle("Test WidgetButtonsRow")
    widget.show()
    sys.exit(app.exec_())



