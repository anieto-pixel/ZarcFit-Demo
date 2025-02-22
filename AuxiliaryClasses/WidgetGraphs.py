"""
Created on Mon Dec 30 08:27:11 2024

Graphs for impedance data visualization:
  - ParentGraph (base class)
  - PhaseGraph
  - BodeGraph
  - ColeColeGraph
  - TimeGraph
  - WidgetGraphs (displays multiple graphs)
"""

import sys
import copy
import numpy as np
import pyqtgraph as pg

from PyQt5.QtWidgets import (
    QApplication, QPushButton, QWidget, QTabWidget, QHBoxLayout,
    QVBoxLayout, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt

# Example import for the type-hinted method below:
# from ModelManual import CalculationResult
# In your real code, ensure CalculationResult is defined or properly imported.
class CalculationResult:
    """Dummy placeholder so this snippet runs independently."""
    def __init__(self):
        self.main_freq = np.array([1, 10, 100])
        self.main_z_real = np.array([100, 80, 60])
        self.main_z_imag = np.array([-50, -40, -30])

        self.special_freq = np.array([10, 50, 90])
        self.special_z_real = np.array([70, 65, 55])
        self.special_z_imag = np.array([-40, -35, -28])

        self.timedomain_freq = np.array([1, 10, 100])
        self.timedomain_time = np.linspace(0, 1, 100)
        self.timedomain_volt = np.sin(2 * np.pi * 10 * self.timedomain_time)


class ParentGraph(pg.PlotWidget):
    """
    A base PlotWidget with methods for:
      - Storing and refreshing 'base' data and 'manual' (dynamic) data
      - Plotting or filtering frequency ranges
      - Overridden methods to transform freq, Z_real, Z_imag into X, Y
    """

    def __init__(self):
        super().__init__()

        # Default data for base and manual plots
        self._base_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([100, 80, 60, 40, 20]),
            'Z_imag': np.array([-50, -40, -30, -20, -10]),
        }
        self._manual_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        }

        # Keep full copies to allow re-expansion after filtering
        self._original_base_data = copy.deepcopy(self._base_data)
        self._original_manual_data = copy.deepcopy(self._manual_data)

        self.setTitle("Parent Graph")
        self.showGrid(x=True, y=True)

        # Plot objects for static (base) and dynamic (manual) lines
        self._static_plot = None
        self._dynamic_plot = None

        # A small auto-scale button in the top-left corner
        self.auto_scale_button = QPushButton("", self)
        self.auto_scale_button.setCheckable(True)
        self.auto_scale_button.setGeometry(10, 10, 10, 10)
        self.auto_scale_button.toggled.connect(self._handle_auto_scale_toggle)
        self.auto_scale_button.setStyleSheet("""
            QPushButton { background-color: lightgray; }
            QPushButton:checked { background-color: rgb(102, 178, 255); }
        """)

        # Flag to avoid recursive auto-ranging calls
        self._auto_range_in_progress = False

        # Connect view changes to a handler so we can re-apply auto-range if needed
        self.plotItem.getViewBox().sigRangeChanged.connect(self._on_view_range_changed)

        # Initial display
        self._refresh_graph()
        self.auto_scale_button.setChecked(True)

        # For optional special markers
        self._special_items = []

    def filter_frequency_range(self, f_min, f_max):
        """
        Filters base and manual data to only show points within [f_min, f_max].
        Always filter from the original datasets so we can re-expand later.
        """
        base_mask = (
            (self._original_base_data['freq'] >= f_min)
            & (self._original_base_data['freq'] <= f_max)
        )
        self._base_data = {
            'freq': self._original_base_data['freq'][base_mask],
            'Z_real': self._original_base_data['Z_real'][base_mask],
            'Z_imag': self._original_base_data['Z_imag'][base_mask],
        }

        manual_mask = (
            (self._original_manual_data['freq'] >= f_min)
            & (self._original_manual_data['freq'] <= f_max)
        )
        self._manual_data = {
            'freq': self._original_manual_data['freq'][manual_mask],
            'Z_real': self._original_manual_data['Z_real'][manual_mask],
            'Z_imag': self._original_manual_data['Z_imag'][manual_mask],
        }

        self._refresh_graph()

    def update_parameters_base(self, freq, Z_real, Z_imag):
        """
        Sets new 'base' data and re-displays both plots.
        Also update the originals so filtering includes the new full dataset.
        """
        self.auto_scale_button.setChecked(False)

        self._base_data = {
            'freq': freq,
            'Z_real': Z_real,
            'Z_imag': Z_imag
        }
        self._original_base_data = copy.deepcopy(self._base_data)

        self._refresh_graph()
        self.auto_scale_button.setChecked(True)

    def update_parameters_manual(self, freq, Z_real, Z_imag):
        """
        Sets new 'manual' (dynamic) data and refreshes only the dynamic plot.
        Also update the originals so filtering includes the new full dataset.
        """
        self._manual_data = {
            'freq': freq,
            'Z_real': Z_real,
            'Z_imag': Z_imag
        }
        self._original_manual_data = copy.deepcopy(self._manual_data)
        self._refresh_plot(self._manual_data, self._dynamic_plot)

    def update_special_points(self, freq_array, z_real_array, z_imag_array):
        """
        Adds or updates special marker points on the graph.
        """
        for item in getattr(self, '_special_items', []):
            self.removeItem(item)
        self._special_items = []

        for i, color in enumerate(['r', 'g', 'c']):
            x, y = self._prepare_xy(
                np.array([freq_array[i]]),
                np.array([z_real_array[i]]),
                np.array([z_imag_array[i]])
            )
            plot_item = self.plot(
                x, y, pen=None,
                symbol='x', symbolSize=12,
                symbolBrush=color, symbolPen=color
            )
            self._special_items.append(plot_item)

    def _prepare_xy(self, freq, z_real, z_imag):
        """
        Transforms impedance data (freq, Z_real, Z_imag) into (x, y) for plotting.
        Default is (Z_real, Z_imag). Subclasses override this if needed.
        """
        return z_real, z_imag

    def _refresh_plot(self, data_dict, plot_item):
        """
        Updates a single plot (static or dynamic) with new data.
        data_dict must contain 'freq', 'Z_real', 'Z_imag'.
        """
        x, y = self._prepare_xy(
            data_dict['freq'],
            data_dict['Z_real'],
            data_dict['Z_imag']
        )
        if plot_item:
            plot_item.setData(x, y)

    def _refresh_graph(self):
        """
        Clears and re-displays both the static and dynamic plots.
        """
        self.clear()

        # Static plot
        self._static_plot = self.plot(
            pen='g',           # green line
            symbol='o',
            symbolSize=5,
            symbolBrush='g'
        )
        self._refresh_plot(self._base_data, self._static_plot)

        # Dynamic plot
        self._dynamic_plot = self.plot(
            pen='b',
            symbol='o',
            symbolSize=7,
            symbolBrush=None
        )
        self._refresh_plot(self._manual_data, self._dynamic_plot)

    def _handle_auto_scale_toggle(self, checked):
        """
        Called when the auto-scale button is toggled.
        If enabled, immediately re-auto-range the view.
        """
        if checked:
            self._apply_auto_scale()

    def _on_view_range_changed(self, view_box, view_range):
        """
        Called when the view's range changes.
        If auto-scale is enabled and this change did not originate
        from our own auto-range call, re-apply auto-range.
        """
        if self.auto_scale_button.isChecked() and not self._auto_range_in_progress:
            self._apply_auto_scale()

    def _apply_auto_scale(self):
        """
        Auto-scales the view based solely on the static (green) plot data.
        """
        x_data, y_data = self._prepare_xy(
            self._base_data['freq'],
            self._base_data['Z_real'],
            self._base_data['Z_imag']
        )
        if x_data.size and y_data.size:
            x_min, x_max = np.min(x_data), np.max(x_data)
            y_min, y_max = np.min(y_data), np.max(y_data)

            self._auto_range_in_progress = True
            self.plotItem.getViewBox().setRange(
                xRange=(x_min, x_max),
                yRange=(y_min, y_max),
                padding=0.1
            )
            self._auto_range_in_progress = False


class PhaseGraph(ParentGraph):
    """
    Plots log10(|phase|) vs. frequency (phase in degrees).
    """

    def __init__(self):
        super().__init__()
        self.setTitle("Phase (Log Scale of Degrees)")
        self.setLabel('bottom', "log10(Freq[Hz])")
        self.setLabel('left', "log10(|Phase|)")

        # Fix axes for demonstration
        self.setYRange(-2, 2, padding=0.08)
        self.setXRange(-1.5, 6, padding=0.05)
        self.getViewBox().invertX(True)

    def _prepare_xy(self, freq, z_real, z_imag):
        freq_log = np.log10(freq)
        phase_deg = np.degrees(np.arctan2(z_imag, z_real))
        # Avoid log of zero by adding a small offset
        phase_log = np.log10(np.abs(phase_deg) + 1e-10)
        return freq_log, phase_log


class BodeGraph(ParentGraph):
    """
    Plots the magnitude of impedance in log scale vs. frequency.
    """

    def __init__(self):
        super().__init__()
        self.setTitle("Bode Graph")
        self.setLabel('bottom', "log10(Freq[Hz])")
        self.setLabel('left', "Log10 Magnitude [dB]")

        self.setYRange(3, 7, padding=0.08)
        self.setXRange(-1.5, 6, padding=0.05)
        self.getViewBox().invertX(True)

    def _prepare_xy(self, freq, z_real, z_imag):
        freq_log = np.log10(freq)
        mag = np.sqrt(z_real**2 + z_imag**2)
        # Using log10(magnitude). If you really want dB, use 20*log10(mag).
        mag_db = np.log10(mag)
        return freq_log, mag_db


class ColeColeGraph(ParentGraph):
    """
    Plots a Nyquist diagram: real(Z) vs. -imag(Z).
    """

    def __init__(self):
        super().__init__()
        self.getPlotItem().setAspectLocked(True, 1)

        self.setTitle("Cole-Cole Graph")
        self.setLabel('bottom', "Z' [Ohms]")
        self.setLabel('left', "-Z'' [Ohms]")

    def _prepare_xy(self, freq, z_real, z_imag):
        return z_real, -z_imag


class TimeGraph(ParentGraph):
    """
    Simple time-domain plot: time vs. voltage.
    """

    def __init__(self):
        super().__init__()
        self.setTitle("Time Domain Graph")
        self.setLabel('bottom', "Time [s]")
        self.setLabel('left', "Voltage")

        # Rebuild the graph to remove default data in the constructor
        self._refresh_graph()

    def _prepare_xy(self, freq, time, volt):
        """
        TODO: Implement proper data processing for the time-domain graph.
        Currently returning dummy data (time, volt) for demo purposes.
        """
        # Create a text item with the placeholder message.
        placeholder = pg.TextItem("Placeholder: Not Implemented", anchor=(0.5, 0.5))
        
        # Position the text in the middle of the data range.
        mid_x = (time[0] + time[-1]) / 2 if len(time) else 0.5
        mid_y = (min(volt) + max(volt)) / 2 if len(volt) else 0.5
        placeholder.setPos(mid_x, mid_y)
        
        # Add the text item to the graph.
        self.addItem(placeholder)
        
        
        return time, volt


class WidgetGraphs(QWidget):
    """
    A widget that displays multiple graphs in a split/tabbed layout:
      - A tabbed area with:
          * Cole-Cole (Nyquist) graph
          * Time-Domain graph
      - To the right, a vertical stack of:
          * Bode graph
          * Phase graph
    """

    def __init__(self):
        super().__init__()
        self._init_graphs()
        self._init_ui()

    def _init_graphs(self):
        """
        Initializes internal graph widgets.
        """
        self._big_graph = ColeColeGraph()
        self._small_graph_1 = BodeGraph()
        self._small_graph_2 = PhaseGraph()
        self._tab_graph = TimeGraph()

    def _init_ui(self):
        """
        Initializes and sets up the UI layout.
        """
        # Create the tab widget
        self._tab_widget = QTabWidget()
        self._tab_widget.addTab(self._big_graph, "Cole Graph")
        self._tab_widget.addTab(self._tab_graph, "T.Domain Graph")
        self._tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._tab_widget.setStyleSheet("QTabWidget::pane { border: none; }")

        # Determine tab bar height for alignment
        tab_bar_height = self._tab_widget.tabBar().sizeHint().height()

        # Create the left panel (tabbed area)
        left_panel = self._create_left_panel()

        # Create the right panel (two smaller graphs)
        right_panel = self._create_right_panel(tab_bar_height)

        # Put everything in a horizontal layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

        self.setLayout(main_layout)

    def _create_left_panel(self):
        """
        Creates the left panel containing the QTabWidget inside a QFrame.
        """
        frame = self._create_frame()
        layout = self._create_vbox_layout(frame, margins=(0, 0, 0, 0))
        layout.addWidget(self._tab_widget)
        return frame

    def _create_right_panel(self, tab_bar_height):
        """
        Creates the right panel containing the two smaller graphs.
        """
        frame = self._create_frame()
        layout = self._create_vbox_layout(frame, margins=(0, tab_bar_height, 0, 0))
        layout.addWidget(self._small_graph_1)
        layout.addWidget(self._small_graph_2)
        return frame

    @staticmethod
    def _create_frame():
        """
        Creates and returns a styled QFrame.
        """
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        return frame

    @staticmethod
    def _create_vbox_layout(parent, margins=(0, 0, 0, 0)):
        """
        Creates and returns a QVBoxLayout with the specified margins.
        """
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(*margins)
        layout.setSpacing(0)
        return layout

    def update_front_graphs(self, freq, z_real, z_imag):
        """
        Updates the base (static) data for the Cole, Bode, Phase graphs.
        """
        self._big_graph.update_parameters_base(freq, z_real, z_imag)
        self._small_graph_1.update_parameters_base(freq, z_real, z_imag)
        self._small_graph_2.update_parameters_base(freq, z_real, z_imag)

    def update_timedomain_graph(self, freq, time, voltage):
        """
        Updates the base (static) data for the time-domain graph.
        """
        self._tab_graph.update_parameters_base(freq, time, voltage)

    def update_manual_plot(self, calc_result: CalculationResult):
        """
        Updates all graphs with the 'manual' (dynamic) data from a CalculationResult.
        """
        freq_main = calc_result.main_freq
        z_real_main = calc_result.main_z_real
        z_imag_main = calc_result.main_z_imag

        # Update manual parameters for Cole/Bode/Phase
        self._big_graph.update_parameters_manual(freq_main, z_real_main, z_imag_main)
        self._small_graph_1.update_parameters_manual(freq_main, z_real_main, z_imag_main)
        self._small_graph_2.update_parameters_manual(freq_main, z_real_main, z_imag_main)

        # Add special markers
        freq_sp = calc_result.special_freq
        z_real_sp = calc_result.special_z_real
        z_imag_sp = calc_result.special_z_imag
        self._big_graph.update_special_points(freq_sp, z_real_sp, z_imag_sp)
        self._small_graph_1.update_special_points(freq_sp, z_real_sp, z_imag_sp)
        self._small_graph_2.update_special_points(freq_sp, z_real_sp, z_imag_sp)

        # Update time-domain graph with manual data
        self._tab_graph.update_parameters_manual(
            calc_result.timedomain_freq,
            calc_result.timedomain_time,
            calc_result.timedomain_volt
        )

    def apply_filter_frequency_range(self, f_min, f_max):
        """
        Filters out data outside [f_min, f_max] for all graphs.
        """
        self._big_graph.filter_frequency_range(f_min, f_max)
        self._small_graph_1.filter_frequency_range(f_min, f_max)
        self._small_graph_2.filter_frequency_range(f_min, f_max)
       #TODO
       #self._tab_graph.filter_frequency_range(f_min, f_max)

# -----------------------------------------------------------------------
#  Quick Test
# -----------------------------------------------------------------------

import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QSlider, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt


def generate_base_data(num_points=50):
    freq = np.logspace(0, 5, num_points)
    z_real = 50 + 10 * np.sqrt(freq)
    z_imag = -5 * np.log10(freq + 1)
    time = np.linspace(0, 1, 200)
    volt = 0.5 * np.sin(2 * np.pi * 5 * time)
    return freq, z_real, z_imag, time, volt


def generate_manual_data(base_data, param1, param2, param3):
    freq, z_real, z_imag, time, volt = base_data
    factor = 1 + param1 / 100
    offset_z = param2 / 10
    offset_v = param3 / 100
    return freq, factor * (z_real + offset_z), factor * (z_imag + offset_z), time, factor * volt + offset_v


class TestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manual Test: Blue line only moves")
        self.graphs = WidgetGraphs()

        # Create sliders and labels using parameter info
        params = [("param1", 20), ("param2", 10), ("param3", 5)]
        self.sliders, self.labels = {}, {}
        slider_layout = QVBoxLayout()
        for name, init in params:
            self.labels[name] = QLabel(f"{name}: {init}")
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(init)
            slider.valueChanged.connect(self._update_blue_line)
            self.sliders[name] = slider
            slider_layout.addWidget(self.labels[name])
            slider_layout.addWidget(slider)

        # Main layout: graphs on left, sliders on right
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.graphs, stretch=1)
        main_layout.addLayout(slider_layout)
        self.setLayout(main_layout)

        # Set up the base (green) data once
        self.base_data = generate_base_data()
        freq, z_real, z_imag, time, volt = self.base_data
        self.graphs.update_front_graphs(freq, z_real, z_imag)
        self.graphs.update_timedomain_graph(freq, time, volt)

        self._update_blue_line()

    def _update_blue_line(self):
        p1 = self.sliders["param1"].value()
        p2 = self.sliders["param2"].value()
        p3 = self.sliders["param3"].value()
        for name, val in zip(["param1", "param2", "param3"], (p1, p2, p3)):
            self.labels[name].setText(f"{name}: {val}")

        freq, z_real, z_imag, time, volt = generate_manual_data(self.base_data, p1, p2, p3)
        for graph in (self.graphs._big_graph, self.graphs._small_graph_1, self.graphs._small_graph_2):
            graph.update_parameters_manual(freq, z_real, z_imag)
        self.graphs._tab_graph.update_parameters_manual(freq, time, volt)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    tester = TestWidget()
    tester.show()
    sys.exit(app.exec_())