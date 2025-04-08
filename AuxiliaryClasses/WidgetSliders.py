import sys
from functools import partial
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFontMetrics

# Updated import for custom sliders.
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks


class WidgetSliders(QWidget):
    """
    A widget that displays multiple sliders side by side, each with a label.
    The labels are color-coded. The widget emits the signal `slider_value_updated`
    when any slider's value changes.
    
    Parameters
    ----------
    slider_configurations : dict
    slider_default_values : list
        List of default values in the same order as slider_configurations.keys().
    """
    
    slider_value_updated = pyqtSignal(str, float)
    slider_was_disabled = pyqtSignal(str, bool)
    all_sliders_values_reseted = pyqtSignal(dict)
    all_sliders_disabling_reseted = pyqtSignal(dict)

    def __init__(self, slider_configurations: dict, slider_default_values: list):
        super().__init__()

        # Map slider keys to default values.
        self.slider_default_values = dict(
            zip(slider_configurations.keys(), slider_default_values)
        )
        self.slider_default_disabled=dict.fromkeys(slider_configurations.keys(), False)
        
        # Create sliders and ensure each is wide enough.
        self.sliders = self._create_sliders(slider_configurations)
        
        # Set sliders to default values.
        self.set_to_default_values()
        self.set_to_default_disabled()
        
        # Build the UI and connect signals.
        self._setup_layout(slider_configurations)
        self._connect_signals()

    # -------------------------------
    # Public Methods
    # -------------------------------
    def get_slider(self, key):
        """Return a slider by its key."""
        return self.sliders.get(key)

    def get_sliders_keys(self):
        """Return all slider keys."""
        return self.sliders.keys()

    def get_all_values(self):
        """
        Return current values of all sliders as a dictionary.
        """
        values = {}
        for key in self.slider_default_values:
            slider = self.sliders[key]
            values[key] = slider.get_value()
        return values

    def set_to_default_values(self):
        """
        Reset all sliders to their default values and emit the updated dict.
        """
        values = {}
        for key, default_value in self.slider_default_values.items():
            slider = self.sliders[key]
            slider.set_value(default_value)
            values[key] = slider.get_value()
        self.all_sliders_values_reseted.emit(values)
        
    def set_default_disabled(self, default_values: list):
        """
        Reset all sliders default deactivation state to fit the given list.
        """
        #ensure that if there are extras, they are all turned to false
        self.slider_default_disabled.update({
            k: v for k, v in zip(self.slider_default_disabled, 
                                  default_values
                                  )})
        self.set_to_default_disabled()
        
    def set_to_default_disabled(self):
        """
        Reset all sliders to their default activation and emit the updated dict.
        """
        for k, state in self.slider_default_disabled.items():
            self.sliders[k].set_is_disabled(state)

    def set_all_variables(self, variables: dict):
        """
        Update sliders based on the provided {key: value} dict.
        Raises ValueError if keys do not match the existing sliders.
        """
        if set(variables.keys()) != set(self.sliders.keys()):
            raise ValueError(
                "WidgetSlider.set_all_variables: Incoming dictionary keys do not match the slider keys in WidgetSliders."
            )
        #here happens the difference
        values = {}
        for key, val in variables.items():
            slider = self.sliders[key]
            slider.set_value_exact(val)
            values[key] = slider.get_value()
        self.all_sliders_values_reseted.emit(values)

    # -------------------------------
    # Private Methods
    # -------------------------------
    def _signal_all_sliders_values_reseted(self):
        """(Placeholder) Signal that all sliders have been reset."""
        pass

    def _create_sliders(self, slider_configurations: dict):
        """
        Create slider widgets based on the configuration.
        Ensures the slider button fits completely.
        """
        sliders = {}
        for key, (slider_type, min_value, max_value, color, num_ticks) in slider_configurations.items():
            slider_widget = slider_type(min_value, max_value, color, num_ticks)
            slider_widget.setFixedWidth(75) #maybe delete?
            sliders[key] = slider_widget
        return sliders

    def _setup_layout(self, slider_configurations: dict):
        """
        Create a horizontal layout. For each slider, create a vertical sub-layout
        with a label and the slider widget.
        """
        main_layout = QHBoxLayout()
    
        # NEW: tighter spacing
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(0, 0, 0, 0) #main_layout.setContentsMargins(0, 0, 15, 0)
    
        for key, slider in self.sliders.items():
            slider_layout = QVBoxLayout()
            label = QLabel(key)
            label.setAlignment(Qt.AlignCenter)
    
            # Style the label with the slider's color.
            slider_color = slider_configurations[key][3]
            label.setStyleSheet(f"color: {slider_color}; font-weight: bold;")
    
            slider_layout.addWidget(label)
            slider_layout.addWidget(slider)
            main_layout.addLayout(slider_layout)
    
        self.setLayout(main_layout)

    def _connect_signals(self):
        """
        Connect each slider's value change signal to the widget's signals.
        """
        for key, slider in self.sliders.items():
            slider.value_changed().connect(partial(self.slider_value_updated.emit, key))
            slider.was_disabled.connect(partial(self.slider_was_disabled.emit, key))


# -------------------------------
# Quick Test
# -------------------------------

if __name__ == "__main__":
    from ConfigImporter import ConfigImporter  # For testing only
    from PyQt5.QtWidgets import QPushButton

    def set_all_to_0(sliders_widget):
        """
        Set all sliders to 0.0.
        """
        new_values = {k: 0.0 for k in sliders_widget.sliders.keys()}
        sliders_widget.set_all_variables(new_values)

    app = QApplication(sys.argv)

    # Load configuration.
    config_file = "config.ini"
    config = ConfigImporter(config_file)

    # Create WidgetSliders.
    sliders_widget = WidgetSliders(config.slider_configurations, config.slider_default_values)

    # Create a button to reset all sliders to 0.0.
    btn_set_0 = QPushButton("Set All Model Vars to 0.0")
    btn_set_0.clicked.connect(lambda: set_all_to_0(sliders_widget))

    # Create a test window.
    test_window = QWidget()
    test_window.setWindowTitle("Test ModelManual & WidgetSliders")
    test_window.setGeometry(100, 100, 1200, 600)

    main_layout = QVBoxLayout(test_window)
    main_layout.addWidget(sliders_widget)
    main_layout.addWidget(btn_set_0)

    # Connect signals to print functions for testing.
    sliders_widget.slider_value_updated.connect(print)
    sliders_widget.slider_was_disabled.connect(print)

    test_window.show()
    sys.exit(app.exec_())

    
    