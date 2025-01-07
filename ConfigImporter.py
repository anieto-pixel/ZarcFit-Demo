# ConfigImporter.py

"""
    Loads configuration data for sliders, default values, secondary variables,
    and file-widget settings from a .ini file, storing them as attributes.

    Parameters
    ----------
    config_file : str
        The path to a .ini config file defining at least the following sections:
          - [SliderConfigurations]
          - [SliderDefaultValues]
          - [InputFileWidget]
          - [SeriesSecondaryVariables]
          - [ParallelModelSecondaryVariables]

    Methods
    -------
    test_config_importer()
        Basic test demonstrating how to create a config file, load it,
        and inspect the results.
"""
import os
import configparser
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks


class ConfigImporter:

    def __init__(self, config_file: str):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file '{config_file}' not found.")

        self.config_file = config_file
        self.slider_configurations = {}
        self.slider_default_values = []
        self.series_secondary_variables = {}
        self.parallel_model_secondary_variables = {}
        self.input_file_widget_config = {}

        self._read_config_file()

    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------

    def _read_config_file(self):
        """
        Internal: Reads and parses the .ini file, populating the class attributes.
        """
        config = configparser.ConfigParser()
        config.optionxform = str  # Preserve the case of keys.
        config.read(self.config_file)

        # SliderConfigurations
        sliders = {}
        for key, value in config["SliderConfigurations"].items():
            parts = value.split(",")
            if len(parts) != 4:
                raise ValueError(f"Invalid slider configuration for '{key}'. Expected 4 comma-separated values.")
            slider_type_str, min_val_str, max_val_str, color = parts
            slider_class = self._safe_import(slider_type_str.strip())
            if slider_class is None:
                raise ValueError(f"Unrecognized slider type '{slider_type_str}' for slider '{key}'.")
            sliders[key.strip()] = (
                slider_class,
                float(min_val_str.strip()),
                float(max_val_str.strip()),
                color.strip()
            )
        self.slider_configurations = sliders

        # SliderDefaultValues
        defaults_str = config["SliderDefaultValues"]["defaults"]
        self.slider_default_values = [float(val.strip()) for val in defaults_str.split(",")]

        # InputFileWidget
        if "InputFileWidget" in config:
            self.input_file_widget_config = {key.strip(): value.strip() for key, value in config["InputFileWidget"].items()}

        # SeriesSecondaryVariables (Independent)
        if "SeriesSecondaryVariables" in config:
            self.series_secondary_variables = {key.strip(): value.strip() for key, value in config["SeriesSecondaryVariables"].items()}

        # ParallelModelSecondaryVariables (Dependent)
        if "ParallelModelSecondaryVariables" in config:
            self.parallel_model_secondary_variables = {key.strip(): value.strip() for key, value in config["ParallelModelSecondaryVariables"].items()}

    @staticmethod
    def _safe_import(class_name: str):
        """
        Returns the slider class reference matching the given class_name.
        If the name is unrecognized, returns None.
        """
        classes = {
            "EPowerSliderWithTicks": EPowerSliderWithTicks,
            "DoubleSliderWithTicks": DoubleSliderWithTicks,
        }
        return classes.get(class_name)
