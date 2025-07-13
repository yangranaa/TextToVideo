import re
import subprocess
import threading

import librosa
import numpy as np
import scipy
import soundfile as sf
from matplotlib import pyplot as plt
from noisereduce import noisereduce
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range
from pydub.silence import detect_silence

from FileTool import sort_files_by_idx, delete_file

import pyrubberband

from Setting import Setting


def get_audio_duration(file_path):
    # 加载音频文件（不加载音频数据，只获取时长）
    y, sr = librosa.load(file_path, sr=None, duration=None)
    # 获取时长（单位：秒）
    return librosa.get_duration(y=y, sr=sr)

def set_audio_speed(y, sr, speed):
    stretched_audio = y
    if speed != 1:
        stretched_audio = pyrubberband.time_stretch(y, sr, speed, rbargs={
            "--fine":" ",
            "--pitch-hq":" ",
            "--centre-focus": " ",
            "-c":"6"
        })

    return stretched_audio

def set_audio_pitch(y, sr, n_steps):
    # 使用pyrubberband进行高质量音调调整  n_steps 正生半音负减半音
    y_shifted = y
    if n_steps != 0:
        y_shifted = pyrubberband.pitch_shift(y, sr, n_steps, rbargs={
            "--fine":" ",
            "--pitch-hq":" ",
            "--centre-focus": " ",
            "-c": "6"
        })

    return y_shifted

def set_audio_volume(y, sr, volume):
    adjusted_y = y

    if volume != 1:
        # 调整音量
        adjusted_y = y * volume

        # 确保信号在合理范围内
        adjusted_y = np.clip(adjusted_y, -1.0, 1.0)

    return adjusted_y

def loop_audio(y, sr, target_duration):
    # 获取音频时长（单位：秒）
    audio_duration = librosa.get_duration(y=y, sr=sr)

    # 计算需要重复的次数
    loop_count = int(np.ceil(target_duration / audio_duration))

    # 循环拼接音频
    looped_audio = np.tile(y, loop_count)

    # 截取到目标时长
    target_samples = int(sr * target_duration)
    looped_audio = looped_audio[:target_samples]

    return looped_audio


def numpy_to_audiosegment(y, sr):
    """将float32 numpy数组(-1到1)转换为AudioSegment"""
    # 缩放并转换为16位整数
    y_int16 = (y * 32767).astype(np.int16)

    # 创建AudioSegment
    return AudioSegment(
        y_int16.tobytes(),
        frame_rate=sr,
        sample_width=2,  # 16位=2字节
        channels=1
    )

def audiosegment_to_float32(audio_segment):
    """将AudioSegment转换为float32 numpy数组(-1到1)"""
    # 获取样本数组
    samples = np.array(audio_segment.get_array_of_samples())

    # 转换为float32并归一化
    y_float = samples.astype(np.float32)
    y_float /= 32768.0  # 16位有符号整数范围

    return y_float


def safe_normalize(y, headroom=0.9):
    """安全归一化，保留动态余量"""
    # 计算RMS和峰值
    rms = np.sqrt(np.mean(y ** 2))
    peak = np.max(np.abs(y))

    # 基于RMS的目标增益
    target_gain = 0.1 / rms  # 目标RMS为-20dBFS

    # 限制增益防止削波
    max_gain = headroom / peak
    gain = min(target_gain, max_gain)

    return y * gain

def cut_silent(audio_data, sr):
    Setting.reload_setting()

    silence_thresh = Setting.get('silence_thresh')
    word_silence_len = Setting.get('word_silence_len')
    line_silence_len = Setting.get('line_silence_len')

    audio = numpy_to_audiosegment(audio_data, sr)

    # 检测所有静音段
    silence_ranges = detect_silence(
        audio,
        silence_thresh=silence_thresh,
        min_silence_len=line_silence_len
    )

    # 处理头部和尾部静音
    start_time = 0
    end_time = len(audio)

    if silence_ranges and silence_ranges[0][0] == 0:
        if silence_ranges[0][1] > line_silence_len:
            start_time = silence_ranges[0][1] - line_silence_len
        else:
            start_time = silence_ranges[0][1]

    if silence_ranges and silence_ranges[-1][1] == len(audio):
        end_time = silence_ranges[-1][0]

    trimmed_audio = audio[start_time:end_time]

    # 检测中间静音段
    mid_silences = detect_silence(
        trimmed_audio,
        silence_thresh=silence_thresh,
        min_silence_len=word_silence_len
    )

    segments = []
    prev_end = 0
    for s, e in mid_silences:
        if s > prev_end:
            segments.append(trimmed_audio[prev_end:s])

        if (e - s) > word_silence_len:
            segments.append(trimmed_audio[s:s+word_silence_len])
        else:
            segments.append(trimmed_audio[s:e])

        prev_end = e

    if prev_end < len(audio):
        segments.append(trimmed_audio[prev_end:])

    # 合并所有片段
    final_audio = AudioSegment.empty()
    for seg in segments:
        final_audio += seg

    # 将处理后的 AudioSegment 转回 NumPy 数组（可选）
    final_audio_np = np.array(final_audio.get_array_of_samples(), dtype=np.float32) / (2 ** 15 - 1)

    return final_audio_np

def enhan_vocal(audio_data, sr):
    Setting.reload_setting()

    # pd = Setting.get('prop_decrease')
    # n_fft = Setting.get('n_fft')
    # win_length = Setting.get('win_length')
    #
    # # 提取前0.5秒作为噪声样本
    # noise_sample = audio_data[:int(sr * 0.5)]
    #
    # # 使用noisereduce进行降噪  根据样本消减噪音
    # cleaned = noisereduce.reduce_noise(
    #     y=audio_data,
    #     sr=sr,
    #     y_noise=noise_sample,
    #     prop_decrease=pd,  # 噪声减少比例
    #     n_fft=n_fft,
    #     win_length=win_length,
    #     stationary=True
    # )

    # low_cut_hz = Setting.get('low_cut_hz')
    # hight_cut_hz = Setting.get('hight_cut_hz')
    # butter_order = Setting.get('butter_order')
    #
    # if butter_order > 0:
    #
    #     # 带阻滤波器消除特定频率毛刺
    #     def butter_bandstop(lowcut, highcut, fs, order=5):
    #         nyq = 0.5 * fs
    #         low = lowcut / nyq
    #         high = highcut / nyq
    #         b, a = scipy.signal.butter(order, [low, high], btype='bandstop')
    #         return b, a
    #
    #     # 应用带阻滤波器 (消除典型的爆音频率)
    #     b, a = butter_bandstop(low_cut_hz, hight_cut_hz, sr, order=butter_order)
    #     audio_data = scipy.signal.filtfilt(b, a, audio_data)
    #

    #
    #
    # threshold_ratio = Setting.get('threshold_ratio')
    # cross_save_ratio = Setting.get('cross_save_ratio')
    #
    #
    # if threshold_ratio > 0:
    #
    #     # 2. 动态压缩减少爆音
    #     threshold = threshold_ratio * np.max(np.abs(audio_data))
    #     audio_data = np.where(
    #         np.abs(audio_data) > threshold,
    #         np.sign(audio_data) * threshold + cross_save_ratio * (audio_data - np.sign(audio_data) * threshold),
    #         audio_data
    #     )
    #
    # # 3. 平滑处理
    # window_size = Setting.get('vocal_window_size')
    # if window_size > 0:
    #     audio_data = np.convolve(audio_data, np.ones(window_size) / window_size, mode='same')

    # plot_frequency_response(audio_data, sr, "Original Spectrum")

    low_cut_hz = Setting.get('low_cut_hz')
    low_cut_order = Setting.get('low_cut_order')
    if low_cut_order > 0:
        sos = scipy.signal.butter(low_cut_order, low_cut_hz, 'highpass', fs=sr, output='sos')
        audio_data = scipy.signal.sosfiltfilt(sos, audio_data)

    audio_eq_on = Setting.get('audio_eq_on')
    if audio_eq_on:
        audio_eq = Setting.get('audio_eq')
        for eq_set in audio_eq:
            if eq_set[1] != 0:
                audio_data = apply_parametric_eq(audio_data, sr, eq_set[0], eq_set[1], eq_set[2])

    audio_compress_on = Setting.get('audio_compress_on')
    if audio_compress_on:
        audio_data = apply_compression(audio_data, sr)

    deesser_on = Setting.get('deesser_on')

    if deesser_on:
        audio_data = deesser(audio_data, sr)

    # plot_frequency_response(audio_data, sr, "Equalized Spectrum")

    return audio_data


def dynamic_range_compressor(audio, sr, threshold=-20.0, ratio=3.0, attack=0.005, release=0.1):
    """无依赖的纯Python动态范围压缩实现"""
    gain = 1.0
    envelope = 0.0
    # 时间常数转换 (秒 -> 样本数)
    attack_coef = np.exp(-1 / (attack * sr))
    release_coef = np.exp(-1 / (release * sr))
    compressed = np.zeros_like(audio)

    for i in range(len(audio)):
        # 计算信号包络 (绝对值 + 平滑)
        abs_sample = np.abs(audio[i])
        envelope = max(abs_sample, envelope * release_coef + abs_sample * (1 - release_coef))

        # dB转换与压缩计算
        envelope_db = 20 * np.log10(envelope + 1e-7)
        if envelope_db > threshold:
            reduction_db = (threshold - envelope_db) * (1 - 1 / ratio)
            target_gain = 10 ** (reduction_db / 20)
        else:
            target_gain = 1.0

        # 应用启动/释放时间
        if target_gain < gain:
            gain = attack_coef * gain + (1 - attack_coef) * target_gain
        else:
            gain = release_coef * gain + (1 - release_coef) * target_gain

        compressed[i] = audio[i] * gain

    return compressed

# 转换为分贝值 (dBFS)
def to_dB(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-6))


def apply_compression(audio_data, sr):
    threshold = Setting.get('compre_threshold')
    ratio = Setting.get('compre_ratio')
    attack = Setting.get('compre_attack')
    release = Setting.get('compre_release')
    makeup_gain = Setting.get('compre_makeup_gain')

    gain = compressor_gain(audio_data, sr, threshold, ratio, attack, release)

    compressed = audio_data * gain

    # 应用整体增益补偿
    makeup_gain_linear = 10 ** (makeup_gain / 20)
    compressed = compressed * makeup_gain_linear

    # 防止削波
    compressed = np.clip(compressed, -1.0, 1.0)

    # 可视化原始音频和压缩后音频
    visualize_audio(audio_data, compressed, sr, threshold)

    return compressed


def visualize_audio(original, compressed, sample_rate, threshold):
    """可视化原始音频和压缩后音频的波形和频谱"""

    plt.figure(figsize=(15, 10))

    # 波形对比
    plt.subplot(2, 1, 1)
    time = np.arange(len(original)) / sample_rate
    plt.plot(time, original, 'b', alpha=0.6, label='原始音频')
    plt.plot(time, compressed, 'r', alpha=0.6, label='压缩后音频')
    plt.axhline(y=10 ** (threshold / 20), color='g', linestyle='--', label=f'阈值 ({threshold} dB)')
    plt.axhline(y=-10 ** (threshold / 20), color='g', linestyle='--')
    plt.title('波形对比')
    plt.xlabel('时间 (秒)')
    plt.ylabel('振幅')
    plt.legend()
    plt.grid(True)

    # 频谱对比
    plt.subplot(2, 1, 2)
    n = len(original)
    freq = np.fft.rfftfreq(n, d=1 / sample_rate)

    # 计算原始音频频谱
    orig_fft = np.abs(np.fft.rfft(original))
    orig_spectrum = 20 * np.log10(np.maximum(orig_fft, 1e-10))

    # 计算压缩后音频频谱
    comp_fft = np.abs(np.fft.rfft(compressed))
    comp_spectrum = 20 * np.log10(np.maximum(comp_fft, 1e-10))

    plt.plot(freq, orig_spectrum, 'b', alpha=0.6, label='原始频谱')
    plt.plot(freq, comp_spectrum, 'r', alpha=0.6, label='压缩后频谱')
    plt.title('频谱对比 (2-5kHz区域为语音清晰度关键)')
    plt.xlabel('频率 (Hz)')
    plt.ylabel('幅度 (dB)')
    plt.xlim(0, 8000)  # 重点关注人声频率范围
    plt.axvspan(2000, 5000, color='yellow', alpha=0.2, label='清晰度关键区域')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('audio_compression_visualization.png')
    plt.show()

def compressor_gain(signal, sr, thresh, ratio, attack_t, release_t):
    dB = to_dB(signal)

    # 计算超出阈值的量
    over_thresh = np.maximum(dB - thresh, 0)

    # 计算需要的增益减少量 (dB)
    gain_reduction = over_thresh * (1 - 1/ratio)

    # 应用启动和释放时间（平滑增益减少）
    smoothed_reduction = np.zeros_like(gain_reduction)

    # 时间常数转换为样本数
    attack_samples = int(attack_t * sr)
    release_samples = int(release_t * sr)

    # 应用平滑
    for i in range(1, len(gain_reduction)):
        if gain_reduction[i] > smoothed_reduction[i-1]:
            # 启动阶段
            smoothed_reduction[i] = smoothed_reduction[i-1] + (gain_reduction[i] - smoothed_reduction[i-1]) / attack_samples
        else:
            # 释放阶段
            smoothed_reduction[i] = smoothed_reduction[i-1] + (gain_reduction[i] - smoothed_reduction[i-1]) / release_samples

    # 计算实际增益 (dB)
    gain_dB = -smoothed_reduction

    # 转换为线性增益值
    gain_linear = 10 ** (gain_dB / 20)

    return gain_linear

# 3. 高频限幅 (防止电流声)
def high_freq_limiter(audio, sr, limit_db=-6.0):
    """高频限幅器"""
    # 分离高频成分
    sos_high = scipy.signal.butter(4, 4000, 'high', fs=sr, output='sos')
    high_band = scipy.signal.sosfiltfilt(sos_high, audio)

    # 应用软削波
    high_band = np.tanh(high_band * 3) / 3

    # 混合低频
    sos_low = scipy.signal.butter(4, 4000, 'low', fs=sr, output='sos')
    low_band = scipy.signal.sosfiltfilt(sos_low, audio)

    return low_band + high_band

def advanced_denoise(audio, sr):
    """多级降噪处理"""
    # 第一级：基础谱减法
    stft = librosa.stft(audio)
    mag, phase = librosa.magphase(stft)

    # 噪声估计（使用前1%的帧）
    noise_frames = mag[:, :int(0.01 * mag.shape[1])]
    noise_profile = np.mean(noise_frames, axis=1, keepdims=True)

    # 谱减
    mag_denoised = np.maximum(mag - 0.8 * noise_profile, 0.001)

    # 第二级：相位感知降噪
    denoised_audio = librosa.istft(mag_denoised * phase)

    # 第三级：自适应陷波滤波器
    sos = scipy.signal.butter(6, [4000, 8000], 'bandstop', fs=sr, output='sos')
    return scipy.signal.sosfiltfilt(sos, denoised_audio)

def apply_parametric_eq(audio, sr, center_freq, gain_db, q_factor):
    """应用参数化均衡器"""
    nyquist = 0.5 * sr
    center = center_freq / nyquist

    # 将dB转换为线性增益
    gain_linear = 10 ** (gain_db / 20.0)

    # 设计滤波器
    b, a = scipy.signal.iirpeak(center, q_factor)

    # 使用零相位滤波
    filtered = scipy.signal.filtfilt(b, a, audio)

    # 更精确的叠加方式
    return audio + (gain_linear - 1) * filtered


def master_limiter(audio, sr, threshold=-1.0, release=50):
    """母带级限制器防止削波"""
    # 初始化
    gain = np.ones(len(audio))
    current_gain = 1.0
    decay = 1 - (1 / (release * 0.001 * sr))  # 基于采样率的衰减

    # 样本级处理
    for i in range(len(audio)):
        sample = audio[i] * current_gain

        # 检查是否超阈值
        if np.abs(sample) > 10 ** (threshold / 20):
            required_gain = (10 ** (threshold / 20)) / np.abs(sample)
            current_gain = min(current_gain, required_gain)

        # 应用增益并缓慢恢复
        audio[i] *= current_gain
        current_gain = min(1.0, current_gain + (1 - current_gain) * decay)

    return audio

def safe_harmonic_enhancement(audio, margin=4, max_hf_gain=6.0):
    """安全的谐波增强，避免噪声放大"""
    # 分频段处理
    low, high = librosa.effects.hpss(audio)

    # 仅对高频部分进行谐波提取
    harmonics = librosa.effects.harmonic(high, margin=margin)

    # 限制高频增益
    hf_gain = min(max_hf_gain, 20 - np.max(librosa.amplitude_to_db(np.abs(harmonics))))
    harmonics *= 10 ** (hf_gain / 20)

    # 安全混合
    return 0.8 * audio + 0.2 * harmonics

def deesser(audio, sample_rate):

    threshold = Setting.get('deesser_threshold')
    ratio = Setting.get('deesser_ratio')
    attack = Setting.get('deesser_attack')
    release = Setting.get('deesser_release')
    low_cut = Setting.get('deesser_low_cut')
    high_cut = Setting.get('deesser_high_cut')
    env_cutoff = Setting.get('deesser_env_cutoff')
    lookahead = Setting.get('deesser_lookahead')
    plot = Setting.get('deesser_plot')

    """
    单通道高品质齿音消除函数
    :param audio: 单声道输入音频信号 (一维数组)
    :param sample_rate: 音频采样率 (Hz)
    :param threshold: 压缩阈值 (dB), 默认-20dB
    :param ratio: 压缩比率, 默认4:1
    :param attack: 启动时间 (秒), 默认5ms
    :param release: 释放时间 (秒), 默认50ms
    :param low_cut: 齿音检测低频截止 (Hz), 默认4kHz
    :param high_cut: 齿音检测高频截止 (Hz), 默认10kHz
    :param env_cutoff: 包络平滑截止频率 (Hz), 默认50Hz
    :param lookahead: 预读时间 (秒), 默认2ms
    :param plot: 是否生成分析图表, 默认False
    :return: 处理后的音频信号
    """
    # 1. 设计SOS带通滤波器
    sos_ess = scipy.signal.butter(
        N=4,
        Wn=[low_cut, high_cut],
        btype='bandpass',
        fs=sample_rate,
        output='sos'
    )

    # 2. 计算包络平滑系数
    rc = 1.0 / (2 * np.pi * env_cutoff)
    env_alpha = np.exp(-1.0 / (rc * sample_rate))

    # 3. 计算动态参数系数
    alpha_attack = np.exp(-1.0 / (attack * sample_rate))
    alpha_release = np.exp(-1.0 / (release * sample_rate))

    # 4. 零相位滤波提取齿音频段
    ess_band = scipy.signal.sosfiltfilt(sos_ess, audio)

    # 5. 计算包络 (绝对值 + 低通滤波)
    envelope = np.abs(ess_band)
    envelope = scipy.signal.lfilter([1 - env_alpha], [1, -env_alpha], envelope)

    # 6. 应用预读缓冲
    lookahead_samples = int(lookahead * sample_rate)
    if lookahead_samples > 0:
        # 向前移动包络信号模拟预读
        envelope = np.concatenate((envelope[lookahead_samples:],
                                   np.full(lookahead_samples, envelope[-1])))

    # 7. 计算增益衰减
    db_envelope = 20 * np.log10(np.clip(envelope, 1e-7, None))
    reduction_db = np.where(
        db_envelope > threshold,
        (threshold - db_envelope) * (1 - 1 / ratio),
        0
    )
    target_gain = 10 ** (reduction_db / 20)

    # 8. 应用启动/释放平滑
    gain_smoothed = np.zeros_like(target_gain)
    current_gain = 1.0

    for i in range(len(target_gain)):
        if target_gain[i] < current_gain:
            current_gain = alpha_attack * current_gain + (1 - alpha_attack) * target_gain[i]
        else:
            current_gain = alpha_release * current_gain + (1 - alpha_release) * target_gain[i]
        gain_smoothed[i] = current_gain

    # 9. 应用增益到原始音频
    processed = audio * gain_smoothed

    # plot = True
    # 10. 可选: 生成分析图表
    if plot:
        plt.figure(figsize=(14, 8))

        # 时域波形对比
        plt.subplot(2, 1, 1)
        plt.plot(audio, 'b', alpha=0.6, label='原始音频')
        plt.plot(processed, 'r', alpha=0.6, label='处理后音频')
        plt.title('波形对比')
        plt.xlabel('样本点')
        plt.ylabel('幅度')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)

        # 频谱对比
        plt.subplot(2, 1, 2)
        f, orig_spec = scipy.signal.welch(audio, fs=sample_rate, nperseg=1024)
        _, proc_spec = scipy.signal.welch(processed, fs=sample_rate, nperseg=1024)
        plt.semilogy(f, orig_spec, 'b', label='原始频谱')
        plt.semilogy(f, proc_spec, 'r', label='处理后频谱')
        plt.xlim(100, 15000)
        plt.axvspan(low_cut, high_cut, color='y', alpha=0.2, label='齿音检测区')
        plt.title('频谱对比 (4-10kHz齿音区域)')
        plt.xlabel('频率 (Hz)')
        plt.ylabel('功率谱密度')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)

        plt.tight_layout()
        plt.show()

    return processed



# test_audio = r"C:\Users\Administrator\Desktop\ttest\合成配音.wav"
# result, sr = librosa.load(test_audio, sr=None, mono=True)
# # result = set_audio_volume(result, sr, 2)
# result = enhan_vocal(result, sr)
#
# sf.write("test_eff.wav", result, sr)

def smooth_gain(target_gain, alpha_attack, alpha_release):
    """应用启动/释放平滑到增益曲线"""
    gain_smoothed = np.zeros_like(target_gain)
    current_gain = 1.0

    for i in range(len(target_gain)):
        if target_gain[i] < current_gain:
            current_gain = alpha_attack * current_gain + (1 - alpha_attack) * target_gain[i]
        else:
            current_gain = alpha_release * current_gain + (1 - alpha_release) * target_gain[i]
        gain_smoothed[i] = current_gain

    return gain_smoothed

# test_audio = r"C:\Users\Administrator\Desktop\ttest\合成配音.wav"
# result, sr = librosa.load(test_audio, sr=None, mono=True)
# # result = set_audio_volume(result, sr, 2)
# result = set_audio_pitch(result, sr, 3)
# # result = enhan_vocal(result, sr)
#
# sf.write("test_eff.wav", result, sr)

def adjust_audio_data(audio_data, sr, **kwargs):
    signal = kwargs.get('signal')

    if kwargs.get('speed'):
        audio_data = set_audio_speed(audio_data, sr, kwargs.get('speed'))

        if signal:
            signal.finished.emit({"value": 1, "total_value": 5})

    if kwargs.get('pitch'):
        audio_data = set_audio_pitch(audio_data, sr, kwargs.get('pitch'))

        if signal:
            signal.finished.emit({"value": 2, "total_value": 5})

    if kwargs.get('cut_silent'):
        audio_data = cut_silent(audio_data, sr)

        if signal:
            signal.finished.emit({"value": 4, "total_value": 5})

    if kwargs.get('enhan_vocal'):
        audio_data = enhan_vocal(audio_data, sr)

    if kwargs.get('volume'):
        audio_data = set_audio_volume(audio_data, sr, kwargs.get('volume'))

        if signal:
            signal.finished.emit({"value": 3, "total_value": 5})


    if kwargs.get('duration'):
        audio_data = loop_audio(audio_data, sr, kwargs.get('duration'))

    if signal:
        signal.finished.emit({"value": 5, "total_value": 5})

    return audio_data


def variation_audio(audio_path, out_path, **kwargs):
    y, sr = librosa.load(audio_path, sr=None)
    audio_data = adjust_audio_data(y, sr, **kwargs)
    delete_file(out_path)
    sf.write(out_path, audio_data, sr)

    signal = kwargs.get('signal')

    if signal:
        signal.finished.emit({"end": True})

def test_rub_on_thread(file):

    def _fun():
        y, sr = librosa.load(file, sr=None)
        set_audio_pitch(y, sr, 2)

    test_thread = threading.Thread(target=_fun)
    test_thread.start()

def milliseconds_to_srt_time_fomat(milliseconds):
    # 将毫秒转换为秒

    # 获取小时、分钟、秒和毫秒
    seconds = milliseconds / 1000.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    # milliseconds = int(seconds % 1000)

    # 格式化为 HH:MM:SS,mmm
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{str(milliseconds)[-3:]}"

def connect_voice_clips(source_path, sound_save_path, srt_save_path=None, text_list=None, **kwargs):
    clips = sort_files_by_idx(source_path)

    signal = kwargs.get('signal')
    kwargs['signal'] = None

    new_data = []
    sampling_rate = 24000
    srt_data = []
    idx = 0
    len_count = 0

    pattern_str = r'[a-zA-Z\u4e00-\u9fff\u3400-\u4dbf\d]'
    pattern = re.compile(pattern_str)

    for clip in clips:

        # 加载片段
        audio_data, sampling_rate = librosa.load(clip, sr=None)
        audio_data = adjust_audio_data(audio_data, sampling_rate, **kwargs)
        new_data.append(audio_data)

        if srt_save_path:
            start_time = int(len_count * 1000 / sampling_rate)
            len_count += len(audio_data)
            end_time = int(len_count * 1000 / sampling_rate)
            # text = Path(clip).stem
            # text = pattern.sub("", text)
            if idx >= len(text_list):
                raise RuntimeError("配音片段与小说内容不匹配。")
            text = text_list[idx]
            find_txts = pattern.findall(text)

            text = ''.join(find_txts)

            srt_data.append((idx + 1, milliseconds_to_srt_time_fomat(start_time), milliseconds_to_srt_time_fomat(end_time), text))

        idx += 1

        if signal:
            signal.finished.emit({"value": idx, "total_value": len(clips)})

    new_data = np.concatenate(new_data)

    # 保存处理后的音频
    sf.write(sound_save_path, new_data, sampling_rate)

    if srt_save_path:
        with open(srt_save_path, 'w', encoding='utf-8') as file:
            for i, (index, start, end, text) in enumerate(srt_data):
                file.write(f"{index}\n")
                file.write(f"{start} --> {end}\n")
                file.write(f"{text}\n\n")

    if signal:
        signal.finished.emit({'end':True})


def gen_srt_file(temp_srt_path, text_list):
    idx = 0
    with open(temp_srt_path, 'w', encoding='utf-8') as file:
        for text in text_list:
            file.write(f"{idx}\n")
            start = milliseconds_to_srt_time_fomat(idx * 3000)
            end = milliseconds_to_srt_time_fomat((idx + 1) * 3000)
            file.write(f"{start} --> {end}\n")
            file.write(f"{text}\n\n")
            idx += 1


def convert_time(time_str):
    time_str = time_str.strip().replace(' ', '')  # 去除空格
    parts = time_str.split(',')
    time_part = parts[0]
    ms_part = parts[1] if len(parts) > 1 else '0'

    # 分割小时、分钟、秒
    hms = time_part.split(':')
    h = int(hms[0]) if len(hms) >= 1 else 0
    m = int(hms[1]) if len(hms) >= 2 else 0
    s = int(hms[2]) if len(hms) >= 3 else 0

    # 处理毫秒
    ms = int(ms_part) if ms_part else 0
    return h * 3600 + m * 60 + s + ms / 1000.0


def parse_time_line(time_line):
    start_str, end_str = [s.strip() for s in time_line.split('-->')]
    return (convert_time(start_str), convert_time(end_str))

def read_srt_file(srt_path):
    blocks = []
    current_index = None
    current_time = None
    current_text = []

    with open(srt_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    for line in lines:
        stripped_line = line.rstrip('\n')  # 去除换行符，保留原有空格
        line_content = stripped_line.strip()  # 判断是否为空行

        if not line_content:  # 处理空行
            if current_index is not None:
                if current_time is not None and current_text:
                    text = '\n'.join(current_text)
                    blocks.append((current_index, current_time, text))
                    current_index = None
                    current_time = None
                    current_text = []
            continue

        if current_index is None:
            if line_content.isdigit():  # 解析索引行
                current_index = int(line_content)
            else:
                # 格式错误，跳过当前块
                current_index = None

        elif current_time is None:
            if '-->' in stripped_line:  # 解析时间行（允许首尾空格）
                current_time = parse_time_line(line_content)
            else:
                # 格式错误，重置当前块
                current_index = None

        else:
            # 收集文字行（保留原有格式）
            current_text.append(stripped_line)

        # 处理文件末尾无空行的情况
    if current_index is not None and current_time is not None and current_text:
        text = '\n'.join(current_text)
        blocks.append((current_index, current_time, text))

    return blocks


# connect_voice_clips(os.getcwd() + '/声音片段/', os.getcwd() + '/合成配音.wav', os.getcwd()+'/音频字幕.srt')
# cut_silent('C:\\Users\\Administrator\\Desktop\\ceshi.mp3')

# duration = librosa.get_duration(y=audio_data, sr=sampling_rate)

# plt.figure(figsize=(12, 4))
# librosa.display.waveshow(non_silent_signal, sr=sampling_rate)
# librosa.display.waveshow(audio_data, sr=sampling_rate)
# plt.show()
