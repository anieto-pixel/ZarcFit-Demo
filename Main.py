"""
Optimized MainWidget and ConfigImporter Classes
"""
# Main.py

import os
import sys
import logging
import inspect
import numpy as np
from sympy import pi
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QLabel, QShortcut
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtGui import QFontMetrics, QFont

# Updated Imports with Renamed Classes
from ConfigImporter import ConfigImporter
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks
from ModelManual import ModelManual
from WidgetOutputFile import WidgetOutputFile
from WidgetInputFile import WidgetInputFile
from WidgetSliders import WidgetSliders
from WidgetButtonsRow import WidgetButtonsRow
from WidgetGraphs import WidgetGraphs
from WidgetTextBar import WidgetTextBar

class MainWidget(QWidget):

    def __init__(self, config_file: str):
        super().__init__()

        """ini file related"""
        # Initialize ConfigImporter
        self.config = ConfigImporter(config_file)
        
        # Store local references to compiled expressions
        self.compiled_expressions = self.config.compiled_expressions
        self.dependent_compiled_expressions = self.config.dependent_compiled_expressions

        self.serial_model_compiled_formula = self.config.serial_model_compiled_formula
        #self.manual_formula_symbols = self.config.manual_formula_symbols


        """Data atributes"""
        # Data placeholders for file & model outputs
        self.file_data = {"freq": [1,2,3,4], "Z_real": None, "Z_imag": None}
        self.modeled_data = {"freq": None, "Z_real": None, "Z_imag": None}

        # Dictionary of variables
        self.v_sliders = dict(zip(self.config.slider_configurations.keys(),
                                  self.config.slider_default_values))  # variables of the sliders
        self.v_second = {}  # variables secondary 

        """Initialize core widgets"""
        print(self.config.input_file)
        self.widget_input_file = WidgetInputFile(self.config.input_file_widget_config)
        self.widget_output_file = WidgetOutputFile()

        self.widget_graphs = WidgetGraphs()

        self.widget_sliders = WidgetSliders(
            self.config.slider_configurations,
            self.config.slider_default_values
        )

        self.widget_buttons = WidgetButtonsRow()

        self.widget_at_bottom = WidgetTextBar(
            self.config.series_secondary_variables.keys(), 
            self.config.parallel_model_secondary_variables.keys()
        )

        """Initialize Models"""
        # Model for manual and automatic computations
        self.model_manual = ModelManual(
            list(self.config.slider_configurations.keys()),
            self.config.slider_default_values
        )

        """Optimize Sliders Signaling"""
        # Initialize a timer for debouncing slider updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._update_sliders_data)
        self.pending_updates = {}
        self.value_labels = {}

        """Methods"""
        # Calculate secondary variables initially
        self._calculate_secondary_variables()
        self.widget_at_bottom._update_text(self.v_second)

        # Layout the UI
        self._initialize_ui()

        """Connect signals """
        # Connecting hotkeys
        self._initialize_hotkeys()

        # Listens for new input file data. Updates dictionaries in main 
        self.widget_input_file.file_data_updated.connect(self._update_file_data)

        # Connects sliders to update handler with debouncing
        self.widget_sliders.slider_value_updated.connect(self._handle_slider_update)

        "initialization 2.0 I guess? No fucking idea of how to roganize this part"
        self.widget_input_file.setup_current_file(self.config.input_file)

    # -----------------------------------------------------------------------
    #  Private UI Methods
    # -----------------------------------------------------------------------

    def _initialize_ui(self):
        """
        Assembles the main layout, placing the top bar and bottom splitter.
        """
        # Top bar with input/output widgets
        top_bar_widget = self._create_file_options_widget()

        # Bottom area: sliders + buttons side by side
        bottom_half_layout = QHBoxLayout()
        bottom_half_layout.addWidget(self.widget_sliders)
        bottom_half_layout.addWidget(self.widget_buttons)
        bottom_half_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to save space
        bottom_half_layout.setSpacing(0)  # Remove spacing to save space
        bottom_half_widget = self._create_widget_from_layout(bottom_half_layout)

        # Bottom-most area: bottom area + text
        bottom_and_text_layout = QVBoxLayout()
        bottom_and_text_layout.addWidget(bottom_half_widget)
        bottom_and_text_layout.addWidget(self.widget_at_bottom)
        bottom_and_text_widget = self._create_widget_from_layout(bottom_and_text_layout)

        # Splitter: top for graphs, bottom for sliders+buttons
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.widget_graphs)
        splitter.addWidget(bottom_and_text_widget)
        splitter.setSizes([500, 300])

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(top_bar_widget)
        main_layout.addWidget(splitter)
        main_layout.setContentsMargins(5, 5, 5, 5)

        self.setLayout(main_layout)

    def _create_file_options_widget(self) -> QWidget:
        """
        Builds the top bar containing the file input and file output widgets.
        """
        layout = QHBoxLayout()
        layout.addWidget(self.widget_input_file)
        layout.addStretch()
        layout.addWidget(self.widget_output_file)
        layout.setContentsMargins(0, 0, 0, 0)
        return self._create_widget_from_layout(layout)


    def _create_widget_from_layout(self, layout: QHBoxLayout) -> QWidget:
        """
        Helper to wrap a given layout into a QWidget.
        """
        container = QWidget()
        container.setLayout(layout)
        return container

    # -----------------------------------------------------------------------
    #  Private Helper Methods
    # -----------------------------------------------------------------------

    def _initialize_hotkeys(self):
        """
        Initializes keyboard shortcuts.
        """
        shortcut_f2 = QShortcut(QKeySequence(Qt.Key_F2), self)
        shortcut_f2.activated.connect(lambda: self.model_manual._fit_model())

        shortcut_f4 = QShortcut(QKeySequence(Qt.Key_F4), self)
        shortcut_f4.activated.connect(self._print_model_parameters)

        shortcut_f5 = QShortcut(QKeySequence(Qt.Key_F5), self)
        shortcut_f5.activated.connect(self._print_model_parameters)


    def _calculate_secondary_variables(self):
        """
        Calculates secondary variables using pre-compiled and dependent expressions.
        Assumes that all functions are validated during initialization.
        """
        if not self.compiled_expressions and not self.dependent_compiled_expressions:
            logging.warning("No compiled expressions available.")
            return

        self.v_second = {}
        slider_keys = self.config.slider_configurations.keys()
        slider_values = [self.v_sliders[key] for key in slider_keys]

        # Compute independent secondary variables (SeriesSecondaryVariables)
        for var, func in self.compiled_expressions.items():
            try:
                self.v_second[var] = func(*slider_values)
            except Exception as e:
                logging.error(f"Error evaluating '{var}': {e}")
                self.v_second[var] = None  # Continue processing other expressions

        # Prepare arguments for dependent expressions
        dependent_args = slider_values + [
            self.v_second.get(var, 0) if self.v_second.get(var) is not None else 0 
            for var in self.config.series_secondary_variables.keys()
        ]

        # Compute dependent secondary variables (ParallelModelSecondaryVariables)
        for var, func in self.dependent_compiled_expressions.items():
            try:
                self.v_second[var] = func(*dependent_args)
            except Exception as e:
                logging.error(f"Error evaluating '{var}': {e}")
                self.v_second[var] = None  # Continue processing other expressions

        logging.info("Secondary variables calculated successfully.")
        # At this point, self.v_second contains all secondary variables with computed values

    # -----------------------------------------------------------------------
    #  Private Connections Methods
    # -----------------------------------------------------------------------

    def _print_model_parameters(self):
        """
        Called when Print is requested 
        """
        content, header = self.model_manual.print_model_parameters()
        self.widget_output_file.write_to_file(content, header)

    def _update_file_data(self, freq: np.ndarray, Z_real: np.ndarray, Z_imag: np.ndarray):
        """
        Called when WidgetInputFile emits new file data.
        """
        print("signal was received")
        
        self.file_data.update(freq=freq, Z_real=Z_real, Z_imag=Z_imag)
        self.widget_graphs.update_graphs(freq, Z_real, Z_imag)
        #self.model_manual.initialize_frequencies(freq)
        
        self.config.set_input_file(self.widget_input_file.get_current_file_path())
        # Assuming model_manual triggers necessary updates

    def _update_modeled_data(self, freq: np.ndarray, Z_real: np.ndarray, Z_imag: np.ndarray):
        """
        Called when ModelManual finishes recalculating with new slider values.
        """
        self.modeled_data.update(freq=freq, Z_real=Z_real, Z_imag=Z_imag)
        self.widget_graphs.update_manual_plot(freq, Z_real, Z_imag)

    def _handle_slider_update(self, key, value):
        """
        Handles incoming slider updates by storing them and starting the debounce timer.
        """
        self.pending_updates[key] = value
        self.update_timer.start(10)  # Adjust the timeout as needed

    def _update_sliders_data(self):
        """
        Processes all pending slider updates at once.
        """
        # Update slider values
        for key, value in self.pending_updates.items():
            self.v_sliders[key] = value
        self.pending_updates.clear()

        # Recalculate secondary variables
        self._calculate_secondary_variables()
        self.widget_at_bottom._update_text(self.v_second)
        
  
        
    
    
    def this_is_a_frequency_loop(self):
        """
        Iterates over all frequencies and evaluates the SerialModelFormula for each.
        Stores the results in a numpy array.
        """
        if self.file_data["freq"] is None:
            logging.warning("No frequency data available to iterate over.")
            return
    
        # Ensure that the serial_model_compiled_formula is available
        if self.serial_model_compiled_formula is None:
            logging.error("SerialModelFormula is not compiled.")
            return
    
        # Retrieve the parameter names from the compiled formula
        try:
            param_names = inspect.signature(self.serial_model_compiled_formula).parameters.keys()
        except Exception as e:
            logging.error(f"Error retrieving parameters from SerialModelFormula: {e}")
            return
    
        # Initialize a list to store results
        serial_model_results = []
    
        # Iterate over each frequency
        for freq in self.file_data["freq"]:
            try:
                # Prepare the arguments by fetching from self.v_sliders and self.v_second
                args = []
                for param in param_names:
                    if param == 'freq':
                        args.append(freq)
                    elif param in self.v_sliders:
                        args.append(self.v_sliders[param])
                    elif param in self.v_second:
                        args.append(self.v_second[param])
                    else:
                        # If the variable is not found, log an error and use np.nan
                        logging.error(f"Variable '{param}' not found in v_sliders or v_second.")
                        args.append(np.nan)
    
                # Evaluate the formula
                result = self.serial_model_compiled_formula(*args)
                serial_model_results.append(result)
    
            except Exception as e:
                logging.error(f"Error evaluating SerialModelFormula for freq={freq}: {e}")
                serial_model_results.append(np.nan)  # Use np.nan to indicate failure
    
        # Convert the list to a numpy array
        self.modeled_data['SerialModel'] = np.array(serial_model_results)
        logging.info("SerialModelFormula evaluated for all frequencies.")

        
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    config_file = "config.ini"

    # MainWindow container
    window = QMainWindow()
    main_widget = MainWidget(config_file)
    window.setCentralWidget(main_widget)
    window.setWindowTitle("Slider with Ticks and Labels (Optimized)")
    main_widget.this_is_a_frequency_loop()
    window.show()

    sys.exit(app.exec_())
