"""
信号生成模块
Signal generation module
"""
import numpy as np
from typing import Dict, Any
from config import SIGNAL_CONFIG

class SignalGenerator:
    """信号生成器类 / Signal generator class"""
    
    def __init__(self):
        self.config = SIGNAL_CONFIG
    
    def generate_1f_noise(self, n: int) -> np.ndarray:
        """生成1/f噪声 / Generate 1/f noise"""
        freqs = np.fft.fftfreq(n)
        freqs[0] = 1e-10  # 避免除零 / avoid division by zero
        
        # 创建1/f谱 / Create 1/f spectrum
        f_noise_spectrum = 1.0 / np.sqrt(np.abs(freqs[1:n//2]))
        full_spectrum = np.concatenate([
            [0],  # 直流分量 / DC component
            f_noise_spectrum,
            f_noise_spectrum[::-1]
        ])[:n//2+1]
        
        # 添加随机相位 / Add random phases
        random_phases = np.random.randn(n//2+1) + 1j * np.random.randn(n//2+1)
        f_noise_spectrum_complex = full_spectrum * random_phases / np.abs(random_phases)
        
        # 逆傅里叶变换得到时域信号 / Inverse FFT to get time-domain signal
        f_noise = np.fft.irfft(f_noise_spectrum_complex, n)
        
        # 归一化 / Normalize
        if np.std(f_noise) > 0:
            f_noise = f_noise / np.std(f_noise)
            
        return f_noise
    
    def generate_simulated_signals(self, node_idx: int, n: int) -> Dict[str, Any]:
        """生成模拟数据节点信号（复杂的射电天文模拟）
        Generate simulated signals (complex radio astronomy simulation)
        """
        t = np.linspace(0, 1, n)
        
        if node_idx == 0:
            # 节点1：纯正弦波信号 / Node 1: pure sine wave
            samples = (np.sin(2 * np.pi * 50 * t) * 30 +
                      np.sin(2 * np.pi * 120 * t) * 15)
            
        elif node_idx == 1:
            # 节点2：高斯白噪声 / Node 2: Gaussian white noise
            samples = np.random.randn(n) * 8
            
        else:
            # 节点3-20：复合脉冲星信号 / Nodes 3-20: composite pulsar-like signal
            # 脉冲星周期脉冲 / Pulsar periodic pulse
            pulse_period = 0.2
            pulse_freq = 1.0 / pulse_period
            pulse_phase = 2 * np.pi * pulse_freq * t
            pulse_phase_mod = pulse_phase % (2 * np.pi)
            pulse = np.exp(-(pulse_phase_mod - np.pi)**2 / 0.3) * 20
            pulse = pulse * (1 + 0.1 * np.sin(2 * np.pi * 0.3 * t))
            
            # 宽带连续谱 / Broadband continuum
            continuum_freq = 20 + (node_idx - 2) * 2
            continuum = np.sin(2 * np.pi * continuum_freq * t) * 10
            
            # 热噪声 / Thermal noise
            thermal_noise = np.random.randn(n) * (3 + (node_idx - 2) * 0.2)
            
            # RFI干扰 / RFI interference
            rfi = np.zeros(n)
            if np.random.random() < 0.4:  # 40%概率出现60Hz干扰 / 40% chance of 60Hz interference
                rfi_freq = 60
                rfi += np.sin(2 * np.pi * rfi_freq * t) * np.random.uniform(8, 15)
            
            if np.random.random() < 0.3:  # 30%概率出现突发干扰 / 30% chance of burst interference
                burst_start = np.random.randint(100, 300)
                burst_duration = np.random.randint(20, 40)
                burst_amplitude = np.random.uniform(10, 20)
                rfi[burst_start:burst_start+burst_duration] += burst_amplitude
            
            # 1/f天空噪声 / 1/f sky noise
            f_noise = self.generate_1f_noise(n) * 6
            
            # 色散效应 / Dispersion effect (simulated)
            dispersion = np.zeros(n)
            for i in range(n):
                freq_factor = 0.5 + 0.5 * (i / n)
                phase_shift = 2 * np.pi * 0.8 * freq_factor * t[i]
                dispersion[i] = np.sin(phase_shift) * 4
            
            # 基线漂移 / Baseline drift
            baseline_drift = np.sin(2 * np.pi * 0.05 * t) * 3
            
            # 组合所有成分 / Combine all components
            samples = (pulse + continuum + thermal_noise + rfi + 
                      f_noise[:n] + dispersion + baseline_drift)
            
            # 量化噪声模拟 / Quantization noise simulation
            quantization_step = 0.3
            samples = np.round(samples / quantization_step) * quantization_step
        
        # 限幅保护 / Clipping protection
        samples = np.clip(samples, 
                         -self.config["max_amplitude"], 
                         self.config["max_amplitude"])
        
        return {
            "samples": samples.tolist(),
            "node_idx": node_idx
        }
    
    def generate_real_data_signals(self, node_idx: int, n: int) -> Dict[str, Any]:
        """真实数据接入接口（预留）
        Real data access interface (reserved)
        用户需在此处读取真实数据（如filterbank文件、SDR流等）并返回samples
        User should implement reading of real data (filterbank, SDR stream, etc.) and return samples
        """
        # 示例：返回全零数据（可替换为实际数据读取）
        # Example: returns zeros (replace with actual data reading)
        samples = np.zeros(n).tolist()
        
        return {
            "samples": samples,
            "node_idx": node_idx
        }
    
    def calculate_statistics(self, samples: np.ndarray) -> Dict[str, float]:
        """计算信号的统计特征 / Calculate signal statistics"""
        rms = float(np.std(samples))
        peak = float(np.max(samples) - np.min(samples))
        
        # 计算频域 / Compute frequency domain
        fft_vals = np.fft.rfft(samples)
        raw_spectrum = np.abs(fft_vals) ** 2
        spectrum_db = 50 + 30 * (raw_spectrum / (np.max(raw_spectrum) + 1e-10))
        peak_freq = float(np.argmax(spectrum_db) * 500 / len(spectrum_db))
        
        return {
            "rms": rms,
            "peak": peak,
            "peakFreq": peak_freq,
            "spectrum": spectrum_db.tolist()
        }
    
    def generate_node_data(self, node_idx: int, node_type: str = "simulated") -> Dict[str, Any]:
        """生成单个节点的完整数据包 / Generate complete data packet for a single node"""
        n = self.config["samples_per_node"]
        
        if node_type == "real":
            # 真实数据节点：使用预留接口 / Real data node: use reserved interface
            signal_data = self.generate_real_data_signals(node_idx, n)
        else:
            # 模拟数据节点：使用复杂的射电天文模拟 / Simulated data node: use complex radio astronomy simulation
            signal_data = self.generate_simulated_signals(node_idx, n)
        
        stats = self.calculate_statistics(np.array(signal_data["samples"]))
        
        return {
            "samples": signal_data["samples"],
            "spectrum": stats["spectrum"],
            "rms": stats["rms"],
            "peak": stats["peak"],
            "peakFreq": stats["peakFreq"]
        }


# 全局信号生成器实例 / Global signal generator instance
signal_gen = SignalGenerator()