# -*- coding: utf-8 -*-
"""
Created on Wed Mar  5 12:36:22 2025

@author: agarcian
"""
import numpy as np
import scipy.signal as sig
from scipy.interpolate import interp1d
from scipy.interpolate import PchipInterpolator
from PyQt5.QtCore import QCoreApplication, QObject, pyqtSignal
from ModelCircuits import ModelCircuitParent, ModelCircuitParallel, ModelCircuitSeries

    
###############################################################################
# v/t class
###############################################################################
#3ensure that exp dat ahas the right keywords, else have a catch or something
class TimeDomainBuilder(QObject):
    
    def __init__(self, model_circuit) -> None:
        
        super().__init__() 
        self.N = 2 ** 12     #number of frequencies, power of 2
        self.T = 4           # Time range for Fourier Transform 
        self.model_circuit = model_circuit  
        self._integral_variables = {}
        
    #-------------------------------------------    
    #   Public Methods
    #-----------------------------------------------
    def get_integral_variables(self):
        return self._integral_variables     
    
    def set_model_circuit(self, model_circuit):
        self.model_circuit=model_circuit

    def run_time_domain(self, params: dict, model_circuit: ModelCircuitParent):
        """
        Calculate time-domain values using a real IFFT.
        """ 
        n_freq = (self.N // 2) #+1
        
        dt = self.T / self.N
        df = 1.0 / self.T

        fmin   = 0
        fmax   = n_freq * df
        freq_even = np.linspace(fmin, fmax, int(n_freq + 1))
        freq_even[0] = 0.001

        z_complex = model_circuit.run_rock(params, freq_even)
        z_complex[0] = z_complex[0].real
        t, volt_down, volt_up=self._fourier_transform(z_complex, dt)       
        
        self._integration_variables(t, volt_down)
        
        index = np.searchsorted(t, self.T//2)
        return freq_even[:index+1], t[:index+1], volt_down[:index+1], volt_up[:index+1]

    def transform_to_time_domain(self,experiment_data):
        """
        Transform experimental data to the time domain. 
        Relies on interpolation to "guess" the values at evenly spaced frequencies.
        Then it applies a real IFFT.
        """
        n_freq = (self.N // 2) #+1
        
        prune= 10 #will only use every 10th element of the array
                #reason beign extrapolate works poorly with size differences
        dt = self.T / (self.N/prune)
        df = 1.0 / self.T

        fmin   = 0
        fmax   = n_freq * df
        freq_even = np.linspace(fmin, fmax, int(n_freq + 1))
        #freq_even[0] = 0.001 #?

        freq_even = freq_even[::prune]
              
        z_interp = self._interpolate_points_for_time_domain(freq_even, experiment_data)
        t, volt_down, volt_up=self._fourier_transform(z_interp, dt)   
        
        index = np.searchsorted(t, self.T//2)
        return freq_even[:index+1], t[:index+1], volt_down[:index+1] 
    
    #--------------------------------------
    #   Private Methods
    #------------------------------------------
    def _interpolate_points_for_time_domain(self, freqs_even: np.ndarray, experiment_data) -> np.ndarray:
        """
        Interpolate measured impedance data for the time-domain transform.
        """
        freq   = experiment_data["freq"]
        z_real = experiment_data["Z_real"]
        z_imag = experiment_data["Z_imag"]
    
    
        # Create interpolation functions that extrapolate outside the measured range.
        interp_real = interp1d(freq, z_real, kind="linear", fill_value="extrapolate")
        interp_imag = interp1d(freq, z_imag, kind="linear", fill_value="extrapolate")
    
#        interp_real = PchipInterpolator(freq, z_real, extrapolate=True)
#        interp_imag = PchipInterpolator(freq, z_imag, extrapolate=True)
    
        # Evaluate the interpolants at the uniformly spaced frequencies.
        z_real_interp = interp_real(freqs_even)
        z_imag_interp = interp_imag(freqs_even)

        return z_real_interp + 1j * z_imag_interp
        """
       
        freq   = np.array(experiment_data["freq"])
        z_real = np.array(experiment_data["Z_real"])
        z_imag = np.array(experiment_data["Z_imag"])
    
        # 1) Remove any freq <= 0
        valid_mask = freq > 0
        freq   = freq[valid_mask]
        z_real = z_real[valid_mask]
        z_imag = z_imag[valid_mask]
    
        # 2) Sort by ascending freq
        sort_idx = np.argsort(freq)
        freq   = freq[sort_idx]
        z_real = z_real[sort_idx]
        z_imag = z_imag[sort_idx]
    
        # 3) Remove duplicates (if you have any)
        unique_mask = np.diff(freq, prepend=-np.inf) != 0
        freq   = freq[unique_mask]
        z_real = z_real[unique_mask]
        z_imag = z_imag[unique_mask]
    
        # 4) Create log space for your data
        log_freq_data = np.log10(freq)
        log_freq_even = np.log10(freqs_even)
    
        # 5) Build PCHIP interpolators
        pchip_real = PchipInterpolator(log_freq_data, z_real, extrapolate=True)
        pchip_imag = PchipInterpolator(log_freq_data, z_imag, extrapolate=True)
    
        z_real_interp = pchip_real(log_freq_even)
        z_imag_interp = pchip_imag(log_freq_even)
    
        return z_real_interp + 1j * z_imag_interp
          """      
        
    def _fourier_transform(self, z_complex: np.ndarray, dt: float):
        """
        Build the single-sided array for IRFFT and perform a real IFFT.
        """       
        b, a = sig.butter(2, 0.45) 
        z_inversefft = np.fft.irfft(z_complex)       #to transform the impedance data from the freq domain to the time domain.
                   #largest value is 0.28       
        z_inversefft = sig.filtfilt(b, a, z_inversefft)   #Applies filter
        t = np.arange(len(z_inversefft)) * dt  # constructs time based on N and dt
 
        volt_up = np.concatenate(([0], np.cumsum(z_inversefft)[:-1]))
        
        time_to_plot_in_seconds=2
        
        index = np.searchsorted(t, time_to_plot_in_seconds, side="right")
        volt_down = volt_up[index]-volt_up
        
        return t, volt_down, volt_up

    def _integration_variables(self, t, v_down):
        
        keys=['V(.1ms)',	'V(1ms)', 'V(10)',	'V(100)','V(200)',	'V(400)',	'V(800)',	'V(1.2s)', 'V(1.6s)']
        seconds=[0.0001,	0.001, 0.01,	0.1, 0.2, 0.4, 0.8, 1.2, 1.6]
        
        for key, mili in zip (keys, seconds):
            index = np.searchsorted(t, mili)
            self._integral_variables[key]=v_down[index]
            
#------------------------------------------------------------------------------
# Test
#------------------------------------------------------------------------------

import numpy as np
from PyQt5.QtCore import QObject
# Import your TimeDomainBuilder class here, or paste the class above this test.

# -------------------------------------------------------------------
# 1) Create a minimal dummy ModelCircuitParent-like class
# -------------------------------------------------------------------
class DummyModelCircuit:
    """
    Simulates a 'model circuit' for testing. 
    The 'run_rock(params, freq_even)' method must return an array of complex impedances.
    """
    def run_rock(self, params, freq_even: np.ndarray) -> np.ndarray:
        # For testing, just return some made-up impedance:
        # z = R + jX, here let's do a frequency-dependent real and imaginary part:
        R = params.get("R", 50)  # default 50 ohms
        X = params.get("X", 10)  # default 10 ohms
        # Let's pretend the imaginary part has a sqrt(f) shape, just for variety
        z_real = np.full_like(freq_even, R, dtype=float)
        z_imag = X * np.sqrt(freq_even)
        return z_real + 1j * z_imag


# -------------------------------------------------------------------
# 2) Manual Test Function
# -------------------------------------------------------------------
def manual_test_time_domain_builder():
    # Create a dummy model circuit instance
    circuit = DummyModelCircuit()

    # Create our builder
    tdb = TimeDomainBuilder(model_circuit=circuit)

    # Check initial N, T, and integral variables
    print("Initial N:", tdb.N)
    print("Initial T:", tdb.T)
    print("Initial integral vars:", tdb.get_integral_variables())

    # -------------------------------------------------------------------
    # 3) Test run_time_domain(...)
    # -------------------------------------------------------------------
    test_params = {"R": 100, "X": 20}  # just a dict of param values
    freq_out, time_out, v_down, v_up = tdb.run_time_domain(test_params, circuit)

    print("\n=== Results from run_time_domain(...) ===")
    print("freq_out:", freq_out[:10], " ... ({} total)".format(len(freq_out)))
    print("time_out:", time_out[:10], " ... ({} total)".format(len(time_out)))
    print("v_down:", v_down[:10], "... ({} total)".format(len(v_down)))
    print("v_up:", v_up[:10], "... ({} total)".format(len(v_up)))

    # Check the newly computed integral variables
    print("Integral variables after run_time_domain call:")
    for k, val in tdb.get_integral_variables().items():
        print(f"  {k} = {val:.4f}")

    # -------------------------------------------------------------------
    # 4) Test transform_to_time_domain(...) with some made-up experiment data
    # -------------------------------------------------------------------
    # Create synthetic frequency/impedance data for demonstration
    # Suppose we have an experimental freq from 1Hz to 100Hz, with some real/imag parts
    experiment_data = {
        "freq":   np.linspace(1, 100, 50),  # 50 points
        "Z_real": np.linspace(80, 120, 50), # just a ramp 80->120
        "Z_imag": np.linspace(-40, -20, 50) # ramp -40->-20
    }

    freq_td, t_td, v_down_td = tdb.transform_to_time_domain(experiment_data)

    print("\n=== Results from transform_to_time_domain(...) ===")
    print("freq_td:", freq_td[:10], " ... ({} total)".format(len(freq_td)))
    print("t_td:", t_td[:10], " ... ({} total)".format(len(t_td)))
    print("v_down_td:", v_down_td[:10], "... ({} total)".format(len(v_down_td)))

    # -------------------------------------------------------------------
    # 5) Done
    # -------------------------------------------------------------------
    print("\nManual test completed with no errors.\n")


# -------------------------------------------------------------------
# 6) Run the test if this file is executed directly
# -------------------------------------------------------------------
if __name__ == "__main__":
    manual_test_time_domain_builder()