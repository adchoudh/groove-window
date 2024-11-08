import tkinter as tk
from tkinter import ttk, messagebox
from pydub import AudioSegment
from pydub.playback import play
import numpy as np
import scipy.signal as signal
import threading
import os
import globals

bands = {'low': 0, 'mid': 0, 'high': 0}
playback_thread = None

def apply_equalizer(samples, sample_rate, bands):
    def butter_bandpass(lowcut, highcut, fs, order=6):
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = signal.butter(order, [low, high], btype='band')
        return b, a

    def butter_lowpass(cutoff, fs, order=6):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = signal.butter(order, normal_cutoff, btype='low')
        return b, a

    def butter_highpass(cutoff, fs, order=6):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = signal.butter(order, normal_cutoff, btype='high')
        return b, a

    b_low, a_low = butter_lowpass(200, sample_rate, 6)
    low_band = signal.lfilter(b_low, a_low, samples)

    b_mid, a_mid = butter_bandpass(500, 2000, sample_rate, 6)
    mid_band = signal.lfilter(b_mid, a_mid, samples)

    b_high, a_high = butter_highpass(5000, sample_rate, 6)
    high_band = signal.lfilter(b_high, a_high, samples)

    gain_low = 10 ** (bands['low'] / 20)
    gain_mid = 10 ** (bands['mid'] / 20)
    gain_high = 10 ** (bands['high'] / 20)
    adjusted_low = low_band * gain_low
    adjusted_mid = mid_band * gain_mid
    adjusted_high = high_band * gain_high

    combined_samples = adjusted_low + adjusted_mid + adjusted_high
    max_abs = np.max(np.abs(combined_samples))
    if max_abs > 1:
        combined_samples /= max_abs

    return combined_samples

def open_equalizer_window():
    global playback_thread
    eq_window = tk.Toplevel()
    eq_window.title("Software Equalizer")

    selected_track = tk.StringVar(value="Track 1")
    bands['low'] = 0
    bands['mid'] = 0
    bands['high'] = 0

    def on_close():
        stop_playback()
        eq_window.destroy()

    eq_window.protocol("WM_DELETE_WINDOW", on_close)

    ttk.Label(eq_window, text="Select Track to Equalize:").pack(pady=5)
    track_options = [f"Track {i+1}" for i in range(10)]
    track_menu = ttk.OptionMenu(eq_window, selected_track, track_options[0], *track_options)
    track_menu.pack()

    slider_frame = ttk.Frame(eq_window)
    slider_frame.pack(pady=10)

    low_label_var = tk.StringVar(value="Low: 0 dB")
    ttk.Label(slider_frame, textvariable=low_label_var).grid(row=0, column=0, padx=10)
    low_slider = ttk.Scale(slider_frame, from_=-18, to=18, orient=tk.HORIZONTAL, length=300,
                           command=lambda val: update_band('low', val, low_label_var))
    low_slider.set(0)
    low_slider.grid(row=1, column=0, padx=10)

    mid_label_var = tk.StringVar(value="Mid: 0 dB")
    ttk.Label(slider_frame, textvariable=mid_label_var).grid(row=0, column=1, padx=10)
    mid_slider = ttk.Scale(slider_frame, from_=-18, to=18, orient=tk.HORIZONTAL, length=300,
                           command=lambda val: update_band('mid', val, mid_label_var))
    mid_slider.set(0)
    mid_slider.grid(row=1, column=1, padx=10)

    high_label_var = tk.StringVar(value="High: 0 dB")
    ttk.Label(slider_frame, textvariable=high_label_var).grid(row=0, column=2, padx=10)
    high_slider = ttk.Scale(slider_frame, from_=-18, to=18, orient=tk.HORIZONTAL, length=300,
                            command=lambda val: update_band('high', val, high_label_var))
    high_slider.set(0)
    high_slider.grid(row=1, column=2, padx=10)

    button_frame = ttk.Frame(eq_window)
    button_frame.pack(pady=10)
    apply_button = ttk.Button(button_frame, text="Apply Equalizer", command=lambda: apply_equalizer_to_track(selected_track.get()))
    apply_button.grid(row=0, column=0, padx=10)
    preview_button = ttk.Button(button_frame, text="Preview Equalized Audio", command=lambda: preview_equalized_audio(selected_track.get()))
    preview_button.grid(row=0, column=1, padx=10)

def update_band(band, value, label_var):
    bands[band] = float(value)
    label_var.set(f"{band.capitalize()}: {value} dB")

def stop_playback():
    global playback_thread
    if playback_thread and playback_thread.is_alive():
        playback_thread.join(0.1)

def apply_equalizer_to_track(track_str):
    track_index = int(track_str.split()[1]) - 1
    if not globals.tracks[track_index]:
        messagebox.showerror("Error", f"No audio loaded in {track_str}.")
        return

    try:
        audio_segment = globals.tracks[track_index]
        sample_rate = audio_segment.frame_rate
        samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
        if audio_segment.channels == 2:
            samples = samples.reshape((-1, 2))
        max_val = 2 ** (audio_segment.sample_width * 8 - 1)
        samples /= max_val
        processed_samples = apply_equalizer(samples, sample_rate, bands)
        if audio_segment.channels == 2:
            processed_samples = processed_samples.flatten()
        processed_samples = (processed_samples * max_val).astype(np.int16)
        combined_audio = AudioSegment(
            processed_samples.tobytes(),
            frame_rate=sample_rate,
            sample_width=audio_segment.sample_width,
            channels=audio_segment.channels
        )
        globals.tracks[track_index] = combined_audio
        globals.original_tracks[track_index] = combined_audio

        file_path = globals.track_file_paths[track_index]
        combined_audio.export(file_path, format=os.path.splitext(file_path)[1][1:], bitrate="320k")

        messagebox.showinfo("Equalizer", f"Equalizer applied to {track_str} successfully.")
    except Exception as e:
        messagebox.showerror("Equalizer Error", f"Failed to apply equalizer:\n{e}")

def preview_equalized_audio(track_str):
    global playback_thread
    track_index = int(track_str.split()[1]) - 1
    if not globals.tracks[track_index]:
        messagebox.showerror("Error", f"No audio loaded in {track_str}.")
        return

    try:
        audio_segment = globals.tracks[track_index]
        sample_rate = audio_segment.frame_rate
        samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
        if audio_segment.channels == 2:
            samples = samples.reshape((-1, 2))
        max_val = 2 ** (audio_segment.sample_width * 8 - 1)
        samples /= max_val
        processed_samples = apply_equalizer(samples, sample_rate, bands)
        if audio_segment.channels == 2:
            processed_samples = processed_samples.flatten()
        processed_samples = (processed_samples * max_val).astype(np.int16)
        combined_audio = AudioSegment(
            processed_samples.tobytes(),
            frame_rate=sample_rate,
            sample_width=audio_segment.sample_width,
            channels=audio_segment.channels
        )

        stop_playback()
        playback_thread = threading.Thread(target=play, args=(combined_audio,), daemon=True)
        playback_thread.start()
    except Exception as e:
        messagebox.showerror("Playback Error", f"Failed to play equalized audio:\n{e}")
