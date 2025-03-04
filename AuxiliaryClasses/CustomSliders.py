import sys
import math
import textwrap
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSlider, QLabel, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QPainter, QFont, QColor, QFontMetrics


class CustomSliders(QWidget):
    """
    A basic vertical slider with labeled ticks and a value label.

    This class provides:
      - A slider from min_value to max_value.
      - Tick markings displayed on the widget's paint event.
      - A label showing the current slider value.
    """

    was_disabled = pyqtSignal(bool)

    def __init__(self, min_value, max_value, colour, number_of_tick_intervals=10):
        super().__init__()

        # Setup slider parameters
        self._min_value = min_value
        self._max_value = max_value
        self.colour = colour
        self.disabled_colour = "gray"
        self.number_of_tick_intervals = number_of_tick_intervals
        self.is_disabled = False
        
        # Declare main UI elements:
        self._slider = None
        self._disable_button = None
        self._layout = None
        
        # Building UI components
        self._build_ui()
        
    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------
    def get_value(self):
        """
        Returns the current integer value of the slider.
        """
        return self._slider.value()

    def set_value(self, value):
        """
        Programmatically sets the slider to a given integer value.
        """
        self._slider.setValue(int(value))
    
    def set_value_exact(self, value):
        """
        Programmatically sets the slider to a given integer value.
        """
        return self.set_value(self)

    def toggle_red_frame(self, state: bool):
        """
        Set a thick red frame around the label of the slider if not already set,
        and remove it if it is set.
        """
        red_border_style = "border: 3px solid red;"
        current_style = self._disable_button.styleSheet()

        if not state:
            # Remove the red border
            new_style = current_style.replace(red_border_style, "")
            self._disable_button.setStyleSheet(new_style)
        else:
            # Append the red border to the current style
            new_style = current_style + " " + red_border_style
            self._disable_button.setStyleSheet(new_style)

    def value_changed(self):
        """
        Exposes the slider's valueChanged signal for external listeners.
        """
        return self._slider.valueChanged
      
    def set_is_disabled(self, state:bool):
        """
        Seets "is disabled" to the given state.Signals.
        """
        
        self.is_disabled = state
        self._react_to_is_disbled_state()
    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------
    # Construction and initialization
    def _build_ui(self):
        
        # Creates main slider
        self._slider = QSlider(Qt.Vertical, self)  # enabled by default

        # Creates disable button with label overlay
        self._create_disable_button()
        self._create_setvalue_box()
        self._connect_signals()
        self._setup_layout()
        self._setup_slider()
        
    def _create_disable_button(self):
        """
        Create the push-button that displays the slider's value and toggles state.
        """
        font_size=12
        
        #create button
        initial_text = str(self._slider.value())
        self._disable_button = QPushButton(initial_text, self)
        self._disable_button.setStyleSheet(f"font-size: {font_size}px;")
        
        #Calculate the width required to display 8 characters.
        font = QFont()
        font.setPointSize(font_size)  # Match the label size
        metrics = self.fontMetrics()
        width= metrics.horizontalAdvance("-0099e+00") + 10  # Add padding
    
        #set button's dimensions
        self._disable_button.setFixedSize(width, 20)
        
    def _create_setvalue_box(self):
        """ 
        Create an imput window to manually set the slider 
        """
        placeholder_text="Set Value"
        self._input_box = QLineEdit()
        self._input_box.setPlaceholderText(placeholder_text)
        
        self._input_box.setFixedWidth(self._disable_button.width())
        self._input_box.setStyleSheet("""
            QLineEdit {
                background-color: lightgrey;
                border: 1px solid lightgrey;
            }
        """)

    def _connect_signals(self):
        """
        Connect internal widget signals to their handlers.
        """
        # Whenever the slider changes, update the label text
        self._slider.valueChanged.connect(self._update_label)

        # Toggling the push-button toggles disabled style
        self._disable_button.clicked.connect(self._toggle_slider)
        #connect set value button
        self._input_box.returnPressed.connect(lambda: self.set_value(self._input_box.text()))

    def _setup_layout(self):
        """
        Create and assign a layout containing the slider and the value label.
        """
        self._layout = QVBoxLayout()
        self._layout.addWidget(self._slider)
        self._layout.addWidget(self._disable_button)
        self._layout.addWidget(self._input_box)
        self.setLayout(self._layout)
        
        # Ensure the widget has a minimum width equal to the button width + padding
        button_min_width = self._disable_button.width()
        self.setMinimumWidth(button_min_width + 3)  # Add small cushioning

    def _setup_slider(self):
        """
        Configure the slider's properties (range, ticks, color).
        """
        self._slider.setRange(self._min_value, self._max_value)
        self._slider.setTickPosition(QSlider.TicksBothSides)

        # Safely set a tick interval (avoid division by zero if ranges are small)
        interval = max(1, (self._max_value - self._min_value) // self.number_of_tick_intervals)
        self._slider.setTickInterval(interval)

        self._update_slider_style(self.colour)
        self.setMinimumWidth(75)

    #Listeners and handers
    def _toggle_slider(self):
        """
        Flip the is_disabled state and update styles. It signals.
        """
        self.is_disabled = not self.is_disabled
        self._react_to_is_disbled_state()

    def _react_to_is_disbled_state(self):
        """
        Adjusts appeareance to toggle state.
        """

        if self.is_disabled:
            # In a "disabled" state: set gray background on label
            self._disable_button.setStyleSheet(
                "background-color: gray;  border: none;"
            )
        else:
            # In an "enabled" state: revert background
            self._disable_button.setStyleSheet(
                "background-color: none;"
            )

        # Update label text based on new slider value
        self._update_label()
        # Emit a signal indicating the disabled state has changed
        self.was_disabled.emit(self.is_disabled)
    
    def _update_slider_style(self, colour: str):
        style = textwrap.dedent(f"""
            QSlider::handle:vertical {{
                background: {colour};
                width: 10px;
                height: 10px;
                border-radius: 20px;
            }}
            QSlider::add-page:vertical {{
                background: #d3d3d3;
                border-radius: 2px;
            }}
        """)
        self._slider.setStyleSheet(style)

    def _update_label(self):
        """
        Update the on-screen label whenever the slider value changes.
        """
        self._disable_button.setText(str(self.get_value()))
        self._input_box.setText(str(self.get_value()))

    def _string_by_tick(self, i):
        """
        Return the string to display next to each tick mark.
        In this default implementation, it's just the integer value.
        """
        return str(i)

    def paintEvent(self, event):
        """
        Draw tick labels for the range of values at fixed intervals.
        """
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setFont(QFont("Arial", 7))
        painter.setPen(QColor(0, 0, 0))

        # Gather slider range/tick info
        min_val = self._slider.minimum()
        max_val = self._slider.maximum()
        tick_interval = self._slider.tickInterval()

        # Calculate available space for drawing
        height = self._slider.height()
        top_off = 5
        bottom_off = 5
        effective_height = height - top_off - bottom_off

        # For each tick step, compute its position and draw text
        for i in range(min_val, max_val + 1, tick_interval):
            tick_pos = (
                height - bottom_off - (effective_height * (i - min_val)) // (max_val - min_val)
            )
            text_rect = QRect(25, tick_pos, 50, 20)
            painter.drawText(text_rect, Qt.AlignCenter, self._string_by_tick(i))
            
#############################################################################

class DoubleSliderWithTicks(CustomSliders):
    """
    A slider that internally uses integer steps but represents
    floating-point values by applying a scale factor.
    """

    # Re-declare a PyQt signal so it emits float instead of int.
    valueChanged = pyqtSignal(float)

    def __init__(self, min_value, max_value, colour, number_of_tick_intervals=10):
        
        self._scale_factor = 1000000
        super().__init__(min_value, max_value, colour, number_of_tick_intervals)
        
    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------
    def get_value(self):
        """
        Return the float value, unscaled.
        """
        return self._slider.value() / self._scale_factor

    def set_value(self, value):
        """
        Set the slider to a float, using the scale factor internally.
        """
        scaled_val = int(value * self._scale_factor)
        self._slider.setValue(scaled_val)

    def set_value_exact(self, value):
        """
        Set the slider to the value given.
        Expects the desired value as an unscaled float.
        """
        self.set_value(value)

    def value_changed(self):
        """
        Return the float-based signal instead of the slider's integer signal.
        """
        return self.valueChanged

    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------
    def _setup_slider(self):
        """
        Overridden to set slider's range as scaled integers. Ticks also scaled.
        """
        int_min = int(self._min_value * self._scale_factor)
        int_max = int(self._max_value * self._scale_factor)
        self._slider.setRange(int_min, int_max)
        self._slider.setTickPosition(QSlider.TicksBothSides)

        interval = max(1, (int_max - int_min) // self.number_of_tick_intervals)
        self._slider.setTickInterval(interval)

        self._update_slider_style(self.colour)
        self.setMinimumWidth(75)
        
    def _connect_signals(self):
        """
        Connect internal widget signals to their handlers.
        """
        # Connect the slider's "raw" integer changes to our float-based signal.
        self._slider.valueChanged.connect(self._emit_corrected_value)
        self._slider.valueChanged.connect(self._update_label)

        # Toggling the push-button toggles disabled style
        self._disable_button.clicked.connect(self._toggle_slider)
        self._input_box.returnPressed.connect(lambda: self.set_value_exact(float(self._input_box.text())))

    def _update_label(self):
        """
        Show the floating-point value with three decimal places.
        """
        self._disable_button.setText(f"{self.get_value():.3f}")
        self._input_box.setText(f"{self.get_value():.3f}")

    def _emit_corrected_value(self, _):
        """
        Emit the float value via self.valueChanged to external listeners.
        """
        self.valueChanged.emit(self.get_value())

    def _string_by_tick(self, i):
        """
        Convert the scaled integer to a string for tick labeling.
        """
        return str(i / self._scale_factor)


##############################################################################
class EPowerSliderWithTicks(DoubleSliderWithTicks):
    def __init__(self, min_value, max_value, colour, number_of_tick_intervals=10):
        self._base_power = 10
        super().__init__(min_value, max_value, colour, number_of_tick_intervals)
        
    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------
    def get_value(self):
        """
        Return 10^n, where n is the float value from the slider.
        """
        n = self._slider.value() / self._scale_factor
        return self._base_power ** n

    def set_value_exact(self, value):
        """
        When the actual desired value is given, find the log10 and pass
        that value to set_value for the slider.
        """
        if value > 0:
            self.set_value(math.log10(value))
        else:
            self.set_value(0)
    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------
    def _update_label(self):
        """
        Display the computed exponent value in scientific notation.
        """
        self._disable_button.setText(f"{self.get_value():.1e}")

    def _string_by_tick(self, i):
        """
        Show each tick label as "1E<exponent>" based on the scaled integer.
        """
        exponent = int(i / self._scale_factor)
        return f"1E{exponent}"


#######################################################################
# ---------------------------------------------------------------------
#  Test
# ---------------------------------------------------------------------
#######################################################################
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSlider, QLabel,
    QHBoxLayout, QLineEdit, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QFont, QColor


class TestSliders(QWidget):
    """
    Main widget to display and manually test all slider types
    in a less repetitive way, with properly captured QLineEdit text.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Slider Manual Test")
        self.setGeometry(100, 100, 1200, 400)

        # Store [Set Value, Min, Max] inputs for each slider type
        self.slider_values = {
            "custom": [None, None, None],
            "double": [None, None, None],
            "epower": [None, None, None],
        }

        # Keep references to slider objects for set_value calls
        self.sliders = {}

        # Keep all info needed to rebuild a slider if Min or Max changes
        self.slider_info = {}

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 1) Custom Slider
        custom_section = self.add_slider_section(
            slider_type="custom",
            slider_class=CustomSliders,
            label_text="Custom Slider",
            min_val=-100, max_val=100, colour="blue", number_of_tick_intervals=9,
            is_float=False
        )
        main_layout.addLayout(custom_section)

        # 2) Double Slider
        double_section = self.add_slider_section(
            slider_type="double",
            slider_class=DoubleSliderWithTicks,
            label_text="Double Slider",
            min_val=-1.0, max_val=1.0, colour="green", number_of_tick_intervals=8,
            is_float=True
        )
        main_layout.addLayout(double_section)

        # 3) E-Power Slider
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
        """
        Creates a slider+label+input-box section.
        slider_type: a string identifier ('custom', 'double', etc.)
        slider_class: the QWidget-based slider class to instantiate
        label_text: text to display above the slider
        min_val, max_val, colour: parameters to pass to slider_class
        is_float: whether inputs should be float or int
        """
        # Outer vertical container
        container = QVBoxLayout()
        container.setSpacing(10)
        container.setContentsMargins(10, 10, 10, 10)

        # Label
        main_label = QLabel(label_text)
        main_label.setAlignment(Qt.AlignCenter)
        main_label.setStyleSheet("font-weight: bold;")
        container.addWidget(main_label)

        # Create the slider
        slider = slider_class(min_val, max_val, colour, number_of_tick_intervals)
        self.sliders[slider_type] = slider

        # Store info so we can rebuild if Min or Max changes
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

        # Connect to print changes
        slider.value_changed().connect(
            lambda val, label=label_text: print(f"{label} Changed: {val}")
        )
        slider.was_disabled.connect(
            lambda val, label=label_text: print(f"{label} Was toggled: {val}")
        )

        # Horizontal layout: slider on the left, input fields on the right
        h_layout = QHBoxLayout()
        h_layout.setSpacing(15)
        h_layout.setContentsMargins(10, 10, 10, 10)

        # Fixed width for slider area to prevent expansion
        slider_container = QVBoxLayout()
        slider_container.setContentsMargins(0, 0, 0, 0)
        slider_container.addWidget(slider)
        slider.setMinimumWidth(100)
        slider.setMaximumWidth(150)
        h_layout.addLayout(slider_container)

        # Remember the layout in slider_info so we can manipulate it later
        self.slider_info[slider_type]["layout"] = h_layout

        # A vertical layout for the three input boxes
        input_layout = QVBoxLayout()
        input_layout.setSpacing(5)
        input_layout.setContentsMargins(10, 10, 10, 10)

        # "Set Value", "Min", "Max"
        input_labels = ["Set Value", "Min", "Max"]
        for i, lbl in enumerate(input_labels):
            single_input_layout = QVBoxLayout()
            single_input_layout.setSpacing(2)
            single_input_layout.setContentsMargins(5, 5, 5, 5)
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
            QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum)
        )
        h_layout.addLayout(input_layout)
        container.addLayout(h_layout)

        return container

    def save_slider_input(self, slider_type, input_index, input_box, is_float):
        """
        Called when user hits 'Enter' in one of the input fields.
        Attempts to convert the text to float or int depending on is_float,
        stores it, and prints the value or error message.

        Additional rules:
          - If this is the "Set Value" field (index=0), call slider.set_value(value)
          - If this is the "Min" field (index=1), replace the old slider with a new one
            using the new min and the old max.
          - If this is the "Max" field (index=2), replace the old slider with a new one
            using the old min and the new max.
        """
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
        """
        Remove the old slider, create a new one with new_min as the minimum
        and the old slider's maximum, then add the new slider to the layout
        in the same place.
        """
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
        """
        Remove the old slider, create a new one with new_max as the maximum
        and the old slider's minimum, then add the new slider to the layout
        in the same place.
        """
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestSliders()
    window.setWindowTitle("CustomSliders Manual Testing")
    window.show()
    sys.exit(app.exec_())
