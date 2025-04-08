# -*- coding: utf-8 -*-
"""
Created on Wed Mar  5 14:08:21 2025

@author: agarcian
"""
import numpy as np
import scipy.optimize as opt
from PyQt5.QtCore import QCoreApplication, QObject, pyqtSignal
from ModelCircuits import ModelCircuitParent, ModelCircuitParallel, ModelCircuitSeries

###############################################################################
# Fit_class 
###############################################################################
class FitBuilder(QObject):
    """
    This class replicates the circuit calculation by evaluating formulas from
    config.ini. It also calculates secondary variables that were previously in Main.
    """
    
    model_manual_values = pyqtSignal(dict)
    
    def __init__(self, experiment_data, model_circuit) -> None:
        super().__init__()
        self._experiment_data = experiment_data
        self._model_circuit = model_circuit  # Injected dependency
        
        self.lower_bounds = {}
        self.upper_bounds = {}
        self.disabled_variables = set()
        self.gaussian_prior = False
        
    # Public Methods (Interface Unchanged)
    def set_bounds(self, slider_configurations: dict) -> None:
        """
        Set the lower and upper bounds for parameters based on slider configurations.
        """
        for key, config in slider_configurations.items():
            if "Power" in str(config[0]):
                self.lower_bounds[key] = 10 ** config[1]
                self.upper_bounds[key] = 10 ** config[2]
            else:
                self.lower_bounds[key] = config[1]
                self.upper_bounds[key] = config[2]
                
    def set_disabled_variables(self, key: str, disabled: bool) -> None:
        """Enable or disable a parameter for the fit based on its key."""
        if disabled:
            self.disabled_variables.add(key)
        else:
            self.disabled_variables.discard(key)
            
    def set_expdata(self, experiment_data: dict) -> None:
        self._experiment_data = experiment_data

    def set_model_circuit(self, model_circuit) -> None:
        """Update the circuit model dependency."""
        self._model_circuit = model_circuit
            
    def fit_model_cole(self, initial_params: dict, prior_weight: float) -> dict:
        """Fit the model using the Cole cost function."""
        return self.fit_model(self._residual_cole, initial_params, prior_weight)

    def fit_model_bode(self, initial_params: dict, prior_weight: float) -> dict:
        """Fit the model using the Bode cost function."""
        return self.fit_model(self._residual_bode, initial_params, prior_weight)
            
    def fit_model(self, residual_func, initial_params: dict, prior_weight: float = 0) -> dict:
        """
        Fit the model using a provided residual function and (optionally) a Gaussian prior
        that penalizes deviation from the initial guess.
        """
        all_keys = list(initial_params.keys())
        free_keys = [k for k in all_keys if k not in self.disabled_variables]
        locked_params = {k: initial_params[k] for k in self.disabled_variables if k in initial_params}
        x0 = self._scale_params(free_keys, initial_params)
        lower_bounds_scaled, upper_bounds_scaled = self._build_bounds(free_keys)
    
        def _residual_wrapper(x_free: np.ndarray) -> np.ndarray:
            free_params = self._descale_params(free_keys, x_free)
            full_params = {**locked_params, **free_params}
    
            try:
                model_residual = residual_func(full_params)
            except ValueError:
                # Return a large penalty if the model evaluation fails.
                return np.ones(10000) * 1e6
    
            if self.gaussian_prior:
                prior_res = self._compute_gaussian_prior(x_free, x0, lower_bounds_scaled, upper_bounds_scaled, prior_weight)
                invalid_penalty = self._compute_invalid_guess_penalty(full_params, prior_weight)
                model_residual = np.concatenate([model_residual, prior_res, invalid_penalty])
            
            return model_residual

        result = opt.least_squares(
            _residual_wrapper,
            x0=x0,
            bounds=(lower_bounds_scaled, upper_bounds_scaled),
            method='trf',
            max_nfev=2000
        )
        best_fit_free = self._descale_params(free_keys, result.x)
        best_fit = {**locked_params, **best_fit_free}
        self.model_manual_values.emit(best_fit)
        return best_fit

    # Private Methods (Interface Unchanged)
    def _residual_cole(self, params: dict) -> np.ndarray:
        """Return the residual vector for the Cole model."""
        freq_array = self._experiment_data["freq"]
        z, _ = self._model_circuit.run_model(params, freq_array)
        z_real, z_imag = z.real, z.imag
        exp_real = self._experiment_data["Z_real"]
        exp_imag = self._experiment_data["Z_imag"]
        weight = self._weight_function(params)
        return np.concatenate([(z_real - exp_real) * weight, (z_imag - exp_imag) * weight])

    def _residual_bode(self, params: dict) -> np.ndarray:
        """Return the residual vector for the Bode model."""
        freq_array = self._experiment_data["freq"]
        z, _ = self._model_circuit.run_model(params, freq_array)
        z_real, z_imag = z.real, z.imag
        z_abs = np.hypot(z_real, z_imag)
        z_phase_deg = np.degrees(np.arctan2(z_imag, z_real))
        exp_real = self._experiment_data["Z_real"]
        exp_imag = self._experiment_data["Z_imag"]
        exp_abs = np.hypot(exp_real, exp_imag)
        exp_phase_deg = np.degrees(np.arctan2(exp_imag, exp_real))
        res_abs = np.log10(z_abs) - np.log10(exp_abs)
        res_phase = np.log10(np.abs(z_phase_deg) + 1e-10) - np.log10(np.abs(exp_phase_deg) + 1e-10)
        weight = self._weight_function(params)
        return np.concatenate([res_abs * weight, res_phase * weight])

    def _weight_function(self, params: dict) -> float:
        """
        Assign dynamic weights to errors based on selected parameters.
        """
        weight = 1
        for key in ["Ph", "Pm", "Pl", "Pef"]:
            weight *= 1 + 3 * np.exp(-15 * params[key])
        return weight
                 
    def _compute_invalid_guess_penalty(self, params: dict, prior_weight: float) -> np.ndarray:
        """
        Returns the penalty array if the guess is invalid, otherwise zeros.
        """
        arbitrary_scaling = 1e4
        deviation = self._invalid_guess(params)
        return deviation * arbitrary_scaling * prior_weight

    def _compute_gaussian_prior(
        self, x_guess: np.ndarray, x0: np.ndarray,
        lower_bounds: np.ndarray, upper_bounds: np.ndarray,
        prior_weight: float, gaussian_fraction: int = 5
    ) -> np.ndarray:
        """
        Calculate the Gaussian prior penalty for each parameter.
        """
        sigmas = (upper_bounds - lower_bounds) * gaussian_fraction
        return prior_weight * ((x_guess - x0) / sigmas)

    def _invalid_guess(self, params: dict) -> np.ndarray:
        """
        Test validity criteria: Fh >= Fm >= Fl.
        Returns positive deviations if invalid, zeros otherwise.
        """
        return np.array([
            max(0.0, params["Fm"] - params["Fh"]),
            max(0.0, params["Fl"] - params["Fm"])
        ])
    
    def _build_bounds(self, free_keys: list) -> (np.ndarray, np.ndarray):
        """
        Build scaled lower and upper bounds arrays for free parameters.
        """
        lower_scaled = self._scale_params(free_keys, self.lower_bounds)
        upper_scaled = self._scale_params(free_keys, self.upper_bounds)
        return lower_scaled, upper_scaled
    
    # ---------- Parameter Scaling ----------
    @staticmethod
    def _scale_params(keys: list, params: dict) -> np.ndarray:
        """
        Convert parameter values into a scaled vector for optimization.
        """
        scaled = []
        for key in keys:
            value = params[key]
            if key.startswith('P'):
                scaled.append(value * 10.0)
            else:
                if value <= 0:
                    raise ValueError(f"Parameter {key} must be > 0; got {value}.")
                scaled.append(np.log10(value))
        return np.array(scaled)

    @staticmethod
    def _descale_params(keys: list, x: np.ndarray) -> dict:
        """
        Convert a scaled vector back to the original parameter dictionary.
        """
        descale = {}
        for i, key in enumerate(keys):
            if key.startswith('P'):
                descale[key] = x[i] / 10.0
            else:
                descale[key] = 10 ** x[i]
        return descale
