import sys
import math
import textwrap
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSlider,
    QLabel, QPushButton, QLineEdit, QSizePolicy, QHBoxLayout, QSpacerItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QPainter, QFont, QColor, QFontMetrics

def get_dpi_scale():
    """
    Compute a scaling factor based on a baseline of 96 DPI.
    This helper is applied to elements not automatically scaled.
    """
    screen = QApplication.primaryScreen()
    if screen:
        logical_dpi = screen.logicalDotsPerInch()
        return 96.0 / logical_dpi
    return 1.0

###############################################################################
# CustomSliders
###############################################################################
class CustomSliders(QWidget):
    was_disabled = pyqtSignal(bool)
    
    def __init__(self, min_value, max_value, colour, number_of_tick_intervals=10):
        super().__init__()
        self._min_value = min_value
        self._max_value = max_value
        self.colour = colour
        self.disabled_colour = "gray"
        self.number_of_tick_intervals = number_of_tick_intervals
        self.is_disabled = False

        self._slider = None
        self._disable_button = None
        self._input_box = None
        self._layout = None

        self._initial_button_style = ""
        self._build_ui()
        
    def sizeHint(self):
        # Provide a compact default size with a lower width hint.
        return QSize(50, 150)
    
    #-----------------------------------------------------------------
    # Public Methods
    #-----------------------------------------------------------------
    def get_value(self):
        return self._slider.value()

    def set_value(self, value):
        self._slider.setValue(int(value))

    def set_value_exact(self, value):
        return self.set_value(value)

    def toggle_red_frame(self, state: bool):
        red_border_style = "border: 3px solid red;"
        current_style = self._disable_button.styleSheet()
        if not state:
            new_style = current_style.replace(red_border_style, "")
            self._disable_button.setStyleSheet(new_style)
        else:
            new_style = current_style + " " + red_border_style
            self._disable_button.setStyleSheet(new_style)

    def value_changed(self):
        return self._slider.valueChanged

    def set_is_disabled(self, state: bool):
        self.is_disabled = state
        self._react_to_is_disbled_state()
        
    #-----------------------------------------------------------------
    # Private Methods
    #-----------------------------------------------------------------
    def _build_ui(self):
        self._slider = QSlider(Qt.Vertical, self)
        self._create_disable_button()
        self._create_setvalue_box()
        self._connect_signals()
        self._setup_layout()
        self._setup_slider()
        
    def _create_disable_button(self):
        scale = get_dpi_scale()
        font = QFont("Arial")
        # CHANGED: Increase base font size from 6 to 10 for a thicker button.
        font.setPixelSize(int(8 * scale))  # <-- This line sets the font size for the disable button.
        self._disable_button = QPushButton(str(self._slider.value()), self)
        self._disable_button.setFont(font)

        metrics = QFontMetrics(font)
        exact_height = metrics.height() + 4
        # CHANGED: The button height is derived from the increased font size.
        self._disable_button.setFixedHeight(int(exact_height * scale))
        self._disable_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # CHANGED: Use a style sheet that now uses the new base size (10*scale).
        base_style = f"""
            QPushButton {{
                font-size: {int(8 * scale)}px;  /* CHANGED: Increased from 6px to 10px */
                padding: 1px;
                margin: 0px;
                border: 1px solid gray;
            }}
        """
        self._disable_button.setStyleSheet(base_style)
        self._initial_button_style = base_style

    def _create_setvalue_box(self):
        scale = get_dpi_scale()
        font = QFont("Arial")
    
        font.setPixelSize(int(8 * scale))  # <-- This line sets the font size for the input box.
        
        self._input_box = QLineEdit()
        self._input_box.setFont(font)
        metrics = QFontMetrics(font)
        exact_height = metrics.height() + 4

        self._input_box.setPlaceholderText("Set Value")
        self._input_box.setAlignment(Qt.AlignCenter)


        self._input_box.setFixedHeight(int(exact_height * scale))
        self._input_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # CHANGED: Update the style sheet with the increased font size.
        self._input_box.setStyleSheet(f"""
            QLineEdit {{
                font-size: {int(8 * scale)}px;  /* CHANGED: Increased from 6px to 10px */
                background-color: lightgrey;
                border: 1px solid gray;
                padding: 1px;
                margin: 0px;
            }}
        """)

    def _connect_signals(self):
        self._slider.valueChanged.connect(self._update_label)
        self._disable_button.clicked.connect(self._toggle_slider)
        self._input_box.returnPressed.connect(lambda: self.set_value(self._input_box.text()))

    def _setup_layout(self):
        # Use minimal spacing and margins for a compact vertical stack.
        self._layout = QVBoxLayout()
        self._layout.setSpacing(2)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.addWidget(self._slider)
        self._layout.addWidget(self._disable_button)
        self._layout.addWidget(self._input_box)
        self.setLayout(self._layout)

    def _setup_slider(self):
        self._slider.setRange(self._min_value, self._max_value)
        self._slider.setTickPosition(QSlider.TicksBothSides)
        interval = max(1, (self._max_value - self._min_value) // self.number_of_tick_intervals)
        self._slider.setTickInterval(interval)
        self._update_slider_style(self.colour)

    def _toggle_slider(self):
        self.is_disabled = not self.is_disabled
        self._react_to_is_disbled_state()

    def _react_to_is_disbled_state(self):
        if self.is_disabled:
            self._disable_button.setStyleSheet("background-color: gray; border: none;")
        else:
            self._disable_button.setStyleSheet(self._initial_button_style)
        self._update_label()
        self.was_disabled.emit(self.is_disabled)

    def _update_slider_style(self, colour: str):
        style = textwrap.dedent(f"""
            QSlider::handle:vertical {{
                background: {colour};
                width: {int(10 * get_dpi_scale())}px;
                height: {int(10 * get_dpi_scale())}px;
                border-radius: {int(10 * get_dpi_scale())}px;
            }}
            QSlider::add-page:vertical {{
                background: #d3d3d3;
                border-radius: {int(2 * get_dpi_scale())}px;
            }}
        """)
        self._slider.setStyleSheet(style)

    def _update_label(self):
        current_val = str(self.get_value())
        self._disable_button.setText(current_val)
        self._input_box.clear()
        self._input_box.setPlaceholderText("Set Value")

    def _string_by_tick(self, i):
        return str(i)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        tick_font = QFont("Arial", int(5 * get_dpi_scale()))
        painter.setFont(tick_font)
        painter.setPen(QColor(0, 0, 0))

        # Use the slider's geometry to compute a dynamic horizontal offset.
        slider_geom = self._slider.geometry()
        text_x = slider_geom.x() + slider_geom.width() + int(5 * get_dpi_scale())

        min_val = self._slider.minimum()
        max_val = self._slider.maximum()
        tick_interval = self._slider.tickInterval()

        height = self._slider.height()
        top_off = int(5 * get_dpi_scale())
        bottom_off = int(5 * get_dpi_scale())
        effective_height = height - top_off - bottom_off

        # Adjust the vertical position relative to the slider's geometry.
        base_y = self._slider.y()
        for i in range(min_val, max_val + 1, tick_interval):
            tick_pos = base_y + height - bottom_off - (effective_height * (i - min_val)) // (max_val - min_val)
            text_rect = QRect(text_x, tick_pos - int(10 * get_dpi_scale()), 
                              int(50 * get_dpi_scale()), int(20 * get_dpi_scale()))
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self._string_by_tick(i))

###############################################################################
# DoubleSliderWithTicks
###############################################################################
class DoubleSliderWithTicks(CustomSliders):
    valueChanged = pyqtSignal(float)

    def __init__(self, min_value, max_value, colour, number_of_tick_intervals=10):
        self._scale_factor = 1000000
        super().__init__(min_value, max_value, colour, number_of_tick_intervals)
        
    def get_value(self):
        return self._slider.value() / self._scale_factor

    def set_value(self, value):
        scaled_val = int(value * self._scale_factor)
        self._slider.setValue(scaled_val)

    def set_value_exact(self, value):
        self.set_value(value)

    def value_changed(self):
        return self.valueChanged

    def _setup_slider(self):
        int_min = int(self._min_value * self._scale_factor)
        int_max = int(self._max_value * self._scale_factor)
        self._slider.setRange(int_min, int_max)
        self._slider.setTickPosition(QSlider.TicksBothSides)
        interval = max(1, (int_max - int_min) // self.number_of_tick_intervals)
        self._slider.setTickInterval(interval)
        self._update_slider_style(self.colour)
        # Remove any forced minimum width so that horizontal dimension is flexible.
        
    def _connect_signals(self):
        self._slider.valueChanged.connect(self._emit_corrected_value)
        self._slider.valueChanged.connect(self._update_label)
        self._disable_button.clicked.connect(self._toggle_slider)
        self._input_box.returnPressed.connect(lambda: self.set_value_exact(float(self._input_box.text())))

    def _update_label(self):
        self._disable_button.setText(f"{self.get_value():.3f}")
        self._input_box.clear()
        self._input_box.setPlaceholderText("Set Value")

    def _emit_corrected_value(self, _):
        self.valueChanged.emit(self.get_value())

    def _string_by_tick(self, i):
        return str(i / self._scale_factor)

###############################################################################
# EPowerSliderWithTicks
###############################################################################
class EPowerSliderWithTicks(DoubleSliderWithTicks):
    def __init__(self, min_value, max_value, colour, number_of_tick_intervals=10):
        self._base_power = 10
        super().__init__(min_value, max_value, colour, number_of_tick_intervals)
        
    def get_value(self):
        n = self._slider.value() / self._scale_factor
        return self._base_power ** n

    def set_value_exact(self, value):
        if value > 0:
            self.set_value(math.log10(value))
        else:
            self.set_value(0)

    def _update_label(self):
        self._disable_button.setText(f"{self.get_value():.1e}")
        self._input_box.clear()
        self._input_box.setPlaceholderText("Set Value")

    def _string_by_tick(self, i):
        exponent = int(i / self._scale_factor)
        return f"1E{exponent}"

###############################################################################
# TestSliders: Main Testing Widget
###############################################################################
class TestSliders(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Slider Manual Test")
        self.setGeometry(100, 100, 800, 400)

        # Store inputs for "Set Value", "Min", "Max" per slider type.
        self.slider_values = {
            "custom": [None, None, None],
            "double": [None, None, None],
            "epower": [None, None, None],
        }
        self.sliders = {}
        self.slider_info = {}
        
        # Use tight spacing and minimal margins for overall layout.
        main_layout = QHBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 1) Custom Slider Section
        custom_section = self.add_slider_section(
            slider_type="custom",
            slider_class=CustomSliders,
            label_text="Custom Slider",
            min_val=-100, max_val=100, colour="blue", number_of_tick_intervals=9,
            is_float=False
        )
        main_layout.addLayout(custom_section)

        # 2) Double Slider Section
        double_section = self.add_slider_section(
            slider_type="double",
            slider_class=DoubleSliderWithTicks,
            label_text="Double Slider",
            min_val=-1.0, max_val=1.0, colour="green", number_of_tick_intervals=8,
            is_float=True
        )
        main_layout.addLayout(double_section)

        # 3) E-Power Slider Section
        epower_section = self.add_slider_section(
            slider_type="epower",
            slider_class=EPowerSliderWithTicks,
            label_text="E-Power Slider",
            min_val=-3, max_val=3, colour="red", number_of_tick_intervals=6,
            is_float=True
        )
        main_layout.addLayout(epower_section)

        self.setLayout(main_layout)

    def add_slider_section(self, slider_type, slider_class,
                           label_text, min_val, max_val, colour,
                           number_of_tick_intervals, is_float=False):
        container = QVBoxLayout()
        container.setSpacing(5)
        container.setContentsMargins(5, 5, 5, 5)

        main_label = QLabel(label_text)
        main_label.setAlignment(Qt.AlignCenter)
        main_label.setStyleSheet("font-weight: bold;")
        container.addWidget(main_label)

        slider = slider_class(min_val, max_val, colour, number_of_tick_intervals)
        self.sliders[slider_type] = slider
        self.slider_info[slider_type] = {
            "slider_class": slider_class,
            "min_val": min_val,
            "max_val": max_val,
            "colour": colour,
            "number_of_tick_intervals": number_of_tick_intervals,
            "is_float": is_float,
            "layout": None,
            "slider_widget": slider,
            "label_text": label_text,
        }

        slider.value_changed().connect(
            lambda val, label=label_text: print(f"{label} Changed: {val}")
        )
        slider.was_disabled.connect(
            lambda val, label=label_text: print(f"{label} Was toggled: {val}")
        )

        # Horizontal layout for slider and input fields.
        h_layout = QHBoxLayout()
        h_layout.setSpacing(5)
        h_layout.setContentsMargins(5, 5, 5, 5)
        
        # Let the slider size naturally.
        slider_container = QVBoxLayout()
        slider_container.setContentsMargins(0, 0, 0, 0)
        slider_container.addWidget(slider)
        h_layout.addLayout(slider_container)

        self.slider_info[slider_type]["layout"] = h_layout

        input_layout = QVBoxLayout()
        input_layout.setSpacing(3)
        input_layout.setContentsMargins(5, 5, 5, 5)

        input_labels = ["Set Value", "Min", "Max"]
        for i, lbl in enumerate(input_labels):
            single_input_layout = QVBoxLayout()
            single_input_layout.setSpacing(2)
            single_input_layout.setContentsMargins(2, 2, 2, 2)
            single_input_layout.setAlignment(Qt.AlignLeft)

            small_label = QLabel(lbl)
            small_label.setAlignment(Qt.AlignLeft)
            small_label.setFixedHeight(20)

            input_box = QLineEdit()
            input_box.setPlaceholderText(lbl)
            input_box.setFixedWidth(80)
            input_box.setMaximumWidth(100)
            input_box.setMinimumWidth(60)

            current_slider_type = slider_type
            current_input_index = i

            input_box.returnPressed.connect(
                lambda box=input_box, idx=current_input_index, st=current_slider_type:
                self.save_slider_input(st, idx, box, is_float)
            )

            single_input_layout.addWidget(small_label)
            single_input_layout.addWidget(input_box)
            input_layout.addLayout(single_input_layout)

        input_layout.addStretch()
        h_layout.addSpacerItem(
            QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum)
        )
        h_layout.addLayout(input_layout)
        container.addLayout(h_layout)

        return container

    def save_slider_input(self, slider_type, input_index, input_box, is_float):
        text = input_box.text()
        try:
            value = float(text) if is_float else int(text)
            self.slider_values[slider_type][input_index] = value
            print(f"{slider_type.capitalize()} input {input_index} saved: {value}")

            if input_index == 0:
                self.sliders[slider_type].set_value(value)
            elif input_index == 1:
                self.replace_slider_min(slider_type, value)
            elif input_index == 2:
                self.replace_slider_max(slider_type, value)
        except ValueError:
            print(f"Invalid input for '{slider_type}' at index {input_index}: {text}")

    def replace_slider_min(self, slider_type, new_min):
        info = self.slider_info[slider_type]
        old_slider = info["slider_widget"]
        layout = info["layout"]

        old_max = info["max_val"]
        colour = info["colour"]
        slider_class = info["slider_class"]
        label_text = info["label_text"]
        number_of_tick_intervals = info["number_of_tick_intervals"]

        info["min_val"] = new_min

        layout.removeWidget(old_slider)
        old_slider.setParent(None)

        new_slider = slider_class(new_min, old_max, colour, number_of_tick_intervals)
        self.sliders[slider_type] = new_slider
        info["slider_widget"] = new_slider

        new_slider.value_changed().connect(
            lambda val, label=label_text: print(f"{label} Changed: {val}")
        )
        layout.insertWidget(0, new_slider)

    def replace_slider_max(self, slider_type, new_max):
        info = self.slider_info[slider_type]
        old_slider = info["slider_widget"]
        layout = info["layout"]

        old_min = info["min_val"]
        colour = info["colour"]
        slider_class = info["slider_class"]
        label_text = info["label_text"]
        number_of_tick_intervals = info["number_of_tick_intervals"]

        info["max_val"] = new_max

        layout.removeWidget(old_slider)
        old_slider.setParent(None)

        new_slider = slider_class(old_min, new_max, colour, number_of_tick_intervals)
        self.sliders[slider_type] = new_slider
        info["slider_widget"] = new_slider

        new_slider.value_changed().connect(
            lambda val, label=label_text: print(f"{label} Changed: {val}")
        )
        layout.insertWidget(0, new_slider)

# Enable high DPI attributes.
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestSliders()
    window.setWindowTitle("CustomSliders Manual Testing")
    window.show()
    sys.exit(app.exec_())




