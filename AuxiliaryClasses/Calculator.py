
from dataclasses import dataclass

import numpy as np
import scipy.optimize as opt
import scipy.signal as sig
from scipy.interpolate import interp1d
from scipy.optimize import Bounds
from scipy.interpolate import PchipInterpolator

from PyQt5.QtCore import QCoreApplication, QObject, pyqtSignal
from ModelCircuits import ModelCircuitParent, ModelCircuitParallel, ModelCircuitSeries
from TimeDomainBuilder import TimeDomainBuilder
from FitBuilder import FitBuilder

# Bounds are scaled. Need to add padding for 0 values, handle Qei,
# and implement a way of making Rinf negative.

@dataclass
class CalculationResult:
    """
    Container for main and special impedance data.
    """
    main_freq: np.ndarray = None  # The frequency array used for the main curve
    main_z_real: np.ndarray = None
    main_z_imag: np.ndarray = None
    
    rock_z_real: np.ndarray = None
    rock_z_imag: np.ndarray = None

    special_freq: np.ndarray = None  # The 3 special frequencies
    special_z_real: np.ndarray = None
    special_z_imag: np.ndarray = None

    timedomain_freq: np.ndarray = None  # Elements used for the time domain plot
    timedomain_time: np.ndarray = None
    timedomain_volt_down: np.ndarray = None
    timedomain_volt_up: np.ndarray = None

###############################################################################
# Calculator
###############################################################################
class Calculator(QObject):
    """
    This class replicates the circuit calculation by evaluating formulas from
    config.ini. It also calculates secondary variables that were previously in Main.
    """
    model_manual_result = pyqtSignal(CalculationResult)

    def __init__(self) -> None:
        super().__init__()
        # Initialize experimental data.
        self._experiment_data = {
            "freq": np.array([1, 10, 100, 1000, 10000]),
            "Z_real": np.zeros(5),
            "Z_imag": np.zeros(5),
        }
        # Initialize the circuit model.
        self._model_circuit = ModelCircuitParallel()
        # Instantiate Fit with both experiment data and the circuit model.
        self.fit_builder = FitBuilder(self._experiment_data, self._model_circuit)
        self.time_domain_builder = TimeDomainBuilder(self._model_circuit)

        # Dictionary for additional fit variables.
        self._fit_variables = {'model': self._model_circuit.name}
        self._calculator_variables = {}

    # Public Methods (Interface Unchanged)
    def initialize_expdata(self, file_data: dict) -> None:
        """Set the experimental data from an external dictionary."""
        
        self._experiment_data = file_data
        self.fit_builder.set_expdata(self._experiment_data)

    def set_rinf_negative(self, state: bool) -> None:
        """Set negative resistance flag in the circuit model."""
        
        self._model_circuit.negative_rinf = state

    def set_gaussian_prior(self, state: bool) -> None:
        """Enable or disable the Gaussian prior for model fitting."""
        
        self.gaussian_prior = state
        self.fit_builder.gaussian_prior = state

    def set_bounds(self, slider_configurations: dict) -> None:
        """
        Set the lower and upper bounds for parameters based on slider configurations.
        """
        self.fit_builder.set_bounds(slider_configurations)

    def set_disabled_variables(self, key: str, disabled: bool) -> None:
        """
        Enable or disable a parameter for the fit based on its key.
        """
        self.fit_builder.set_disabled_variables(key, disabled)

    def get_latest_secondaries(self) -> dict:
        """Return the most recent dictionary of secondary variables."""
        
        return dict(self._model_circuit.par_second | self._calculator_variables)

    def get_model_parameters(self) -> dict:
        """
        Return the combined dictionary of model parameters, integrating:
        """
        integral_variables = self.time_domain_builder.get_integral_variables()
        model_variables = self._model_circuit.q | self._model_circuit.par_second | self._model_circuit.par_other_sec
        fit_variables = self._fit_variables
        calc_variables = self._calculator_variables
        
        return fit_variables | model_variables | integral_variables | calc_variables

    def switch_circuit_model(self, state: bool) -> None:
        """
        Switch the circuit model:
          - True selects ModelCircuitSeries.
          - False selects ModelCircuitParallel.
        """
        neg_rinf, old_q, old_vsec, old_ovsec = self._model_circuit.init_parameters()
        if state:
            self._model_circuit = ModelCircuitSeries(
                negative_rinf=neg_rinf,
                q=dict(old_q),
                par_second=dict(old_vsec),
                par_other_sec=dict(old_ovsec)
            )
        else:
            self._model_circuit = ModelCircuitParallel(
                negative_rinf=neg_rinf,
                q=dict(old_q),
                par_second=dict(old_vsec),
                par_other_sec=dict(old_ovsec)
            )
        self.time_domain_builder.set_model_circuit(self._model_circuit)
        self.fit_builder.set_model_circuit(self._model_circuit)

    def fit_model_cole(self, initial_params: dict) -> dict:
        """Fit the model using the Cole cost function."""
        
        prior_weight = 10 ** 6
        return self.fit_builder.fit_model_cole(initial_params, prior_weight)

    def fit_model_bode(self, initial_params: dict) -> dict:
        """Fit the model using the Bode cost function."""
        
        prior_weight = 400
        return self.fit_builder.fit_model_bode(initial_params, prior_weight)

    def run_model_manual(self, params: dict) -> CalculationResult:
        """
        Run the model with the given parameters.

        1) Compute main impedance arrays over the experimental frequencies.
        2) Compute special frequencies and their impedance.
        3) Compute the time-domain response.
        4) Pack all results into a CalculationResult and emit a signal.
        """
        freq_array = self._experiment_data["freq"]
        z_experimental = self._experiment_data["Z_real"].copy() + 1j * self._experiment_data["Z_imag"].copy()
        
        # Calculate Z for the full model, and for the rock alone.
        z, _ = self._model_circuit.run_model(params, freq_array)
        z_real, z_imag = z.real, z.imag
        
        rock_z = self._model_circuit.estimate_rock(params, freq_array, z_experimental)
        rock_z_real, rock_z_imag = rock_z.real, rock_z.imag

        special_freq, spec_zr, spec_zi = self._calculate_special_frequencies(params)
        
        # Time domain response.
        t_freq, t_time, t_volt_down, t_volt_up = self.run_time_domain(params)

        result = CalculationResult(
            main_freq=freq_array,
            main_z_real=z_real,
            main_z_imag=z_imag,
            
            rock_z_real=rock_z_real,
            rock_z_imag=rock_z_imag,
            
            special_freq=special_freq,
            special_z_real=spec_zr,
            special_z_imag=spec_zi,
            
            timedomain_freq=t_freq,
            timedomain_time=t_time,
            timedomain_volt_down=t_volt_down,
            timedomain_volt_up=t_volt_up
        )
        
        self.model_manual_result.emit(result)
        self._update_fit_variables(z_real, z_imag, params)
        return result

    def run_time_domain(self, params: dict):
        """
        Calculate time-domain values using a real IFFT.
        """
        return self.time_domain_builder.run_time_domain(params, self._model_circuit)

    def transform_to_time_domain(self):
        """
        Transform experimental data to time domain.
        """
        #todo Do nto send experiemtn data, send extrapolated rock
        
        return self.time_domain_builder.transform_to_time_domain(self._experiment_data)
    
    """
    def transform_to_time_domain(self, parameters: dict):
        #todo Do nto send experiemtn data, send extrapolated rock
        freq_array = self._experiment_data['freq']
        impedance = self._experiment_data['Z_real'] + 1j*self._experiment_data['Z_imag']
        estimate_rock_z= self.circuit.estimate_rock(parameters, freq_array, impedance)
        
        estimate_rock_data = {
            "freq":freq_array,
            "Z_real":estimate_rock_z.real,
            "Z_imag":estimate_rock_z.imag,
            }
        return self.time_domain_builder.transform_to_time_domain(estimate_rock_data)
    """

    # Private Methods
    def _calculate_special_frequencies(self, params: dict):
        
        fixed_special_frequencies = np.array([0.1])  # Point of interest, f = 0.1Hz
        dynamic_special_freq = self._get_special_freqs(params)
    
        fsf_z, _ = self._model_circuit.run_model(params, fixed_special_frequencies, old_par_second=True)
        dsf_z, _ = self._model_circuit.run_model(params, dynamic_special_freq, old_par_second=True)
    
        # Adding reference resistance to the dictionary
        self._calculator_variables['R01'] = float(fsf_z.real[0])
    
        special_freq = np.concatenate((dynamic_special_freq, fixed_special_frequencies))
        spec_zr = np.concatenate((dsf_z.real, fsf_z.real))
        spec_zi = np.concatenate((dsf_z.imag, np.zeros_like(fsf_z.real)))
    
        return special_freq, spec_zr, spec_zi

    def _get_special_freqs(self, slider_values: dict) -> np.ndarray:
        """
        Return special frequency points based on slider values.
        """
        return np.array([
            slider_values["Fh"],
            slider_values["Fm"],
            slider_values["Fl"],
        ], dtype=float)
    
    def _update_fit_variables(self, z_real, z_imag, params: dict) -> None:
        """
        Update internal fit variables such as mismatch and resistance at 0.1Hz.
        """
        exp_complex = self._experiment_data["Z_real"] + 1j * self._experiment_data["Z_imag"]
        calc_complex = z_real + 1j * z_imag
        mismatch = np.sum(np.abs(exp_complex - calc_complex) ** 2)
        self._fit_variables['mismatch'] = mismatch
        
        # Compute resistance at 0.1Hz.
        z_1Hz = self._model_circuit.run_model(params, [0.1])[0]
        self._fit_variables['Res.1Hz'] = float(abs(z_1Hz.real))
        
        freq_array = self._experiment_data["freq"]
        self._fit_variables['Fhigh'] = freq_array[0]
        self._fit_variables['Flow'] = freq_array[-1]


###############################################################################
#   Test    
###############################################################################
