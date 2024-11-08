import tkinter as tk
from tkinter import ttk, messagebox
import globals
from audio_processing import (
    load_audio, play_all_audio, pause_audio, resume_audio,
    adjust_volume, save_project, load_project, export_project_as_mp3
)
from trim_function import open_trim_window
import os
import subprocess
import sys
import time
from pydub import AudioSegment

def open_temp_directory():
    path = globals.TEMP_DIR
    if os.path.exists(path):
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    else:
        messagebox.showerror("Error", "Session Audios directory does not exist.")

def open_equalizer():
    from equalizer import open_equalizer_window
    open_equalizer_window()

def reload_track(track_index):
    file_path = globals.track_file_paths[track_index]
    if file_path and os.path.exists(file_path):
        try:
            audio = AudioSegment.from_file(file_path)
            globals.original_tracks[track_index] = audio
            globals.tracks[track_index] = audio
            duration_seconds = audio.duration_seconds
            globals.track_durations[track_index] = duration_seconds
            duration_formatted = format_duration(duration_seconds)
            filename = os.path.basename(file_path)
            globals.track_labels[track_index].config(text=f"{filename} ({duration_formatted})")
        except Exception as e:
            messagebox.showerror("Reload Track", f"Failed to reload track {track_index + 1}:\n{e}")

def format_duration(seconds):
    minutes = int(seconds) // 60
    seconds = int(seconds) % 60
    return f"{minutes}:{seconds:02d}"

def check_for_updates():
    for i in range(10):
        file_path = globals.track_file_paths[i]
        if file_path and os.path.exists(file_path):
            last_mod_time = globals.last_mod_times[i]
            current_mod_time = os.path.getmtime(file_path)
            if last_mod_time is None:
                globals.last_mod_times[i] = current_mod_time
            elif current_mod_time != last_mod_time:
                globals.last_mod_times[i] = current_mod_time
                reload_track(i)
    globals.window.after(1000, check_for_updates)

def setup_main_window():
    globals.window = tk.Tk()
    globals.window.title("Groove Window")
    globals.window.geometry("1920x1080")
    globals.window.grid_rowconfigure(0, weight=0)
    globals.window.grid_rowconfigure(1, weight=1)
    globals.window.grid_rowconfigure(2, weight=1)
    globals.window.grid_columnconfigure(0, weight=1)

    control_frame = ttk.Frame(globals.window)
    control_frame.grid(row=0, column=0, pady=10)
    globals.bpm_var = tk.IntVar(value=120)
    bpm_spinbox = ttk.Spinbox(control_frame, from_=40, to=240, textvariable=globals.bpm_var, width=6)
    bpm_spinbox.grid(row=0, column=0, padx=10)
    bpm_label = ttk.Label(control_frame, text="BPM")
    bpm_label.grid(row=0, column=1, padx=5)

    play_all_button = ttk.Button(control_frame, text="Play All", command=play_all_audio)
    play_all_button.grid(row=0, column=2, padx=10)
    pause_button = ttk.Button(control_frame, text="Pause", command=pause_audio)
    pause_button.grid(row=0, column=3, padx=10)
    resume_button = ttk.Button(control_frame, text="Resume", command=resume_audio)
    resume_button.grid(row=0, column=4, padx=10)
    save_button = ttk.Button(control_frame, text="Save Project", command=save_project)
    save_button.grid(row=0, column=5, padx=10)
    load_button = ttk.Button(control_frame, text="Load Project", command=load_project)
    load_button.grid(row=0, column=6, padx=10)
    export_button = ttk.Button(control_frame, text="Export as MP3", command=export_project_as_mp3)
    export_button.grid(row=0, column=7, padx=10)

    track_frame = ttk.Frame(globals.window, padding="10")
    track_frame.grid(row=1, column=0, sticky="nsew")
    globals.track_labels = []

    for track in range(10):
        frame = ttk.Frame(track_frame)
        frame.grid(row=track, column=0, padx=10, pady=10, sticky="w")
        label = ttk.Label(frame, text=f"Track {track + 1}", width=40)
        label.pack(side="left")
        globals.track_labels.append(label)
        load_button = ttk.Button(frame, text="Load Audio", command=lambda t=track: load_audio(t))
        load_button.pack(side="left", padx=5)

    mixer_frame = ttk.Frame(globals.window, padding="10")
    mixer_frame.grid(row=2, column=0, sticky="nsew")
    mixer_frame.grid_columnconfigure(0, weight=1)
    mixer_frame.grid_columnconfigure(1, weight=0)

    mixer_inner_frame = ttk.Frame(mixer_frame)
    mixer_inner_frame.grid(row=0, column=0, sticky="sw")

    globals.mixer_sliders = []
    globals.volume_meters = []
    globals.db_labels = []

    for i in range(10):
        row = i // 5
        column = i % 5
        channel_frame = ttk.Frame(mixer_inner_frame)
        channel_frame.grid(row=row, column=column, padx=5, pady=5)
        ttk.Label(channel_frame, text=f"Channel {i + 1}").pack()

        slider_meter_frame = ttk.Frame(channel_frame)
        slider_meter_frame.pack()

        mixer_slider = ttk.Scale(
            slider_meter_frame,
            orient="horizontal",
            length=150,
            from_=0.0,
            to=1.0,
            command=lambda vol, idx=i: adjust_volume(idx, vol)
        )
        mixer_slider.set(1.0)
        mixer_slider.pack()

        globals.mixer_sliders.append(mixer_slider)

        volume_meter = ttk.Progressbar(
            slider_meter_frame,
            orient="horizontal",
            length=150,
            mode="determinate",
            maximum=100
        )
        volume_meter.pack(pady=2)
        globals.volume_meters.append(volume_meter)

        db_label = ttk.Label(channel_frame, text="-inf dB")
        db_label.pack()
        globals.db_labels.append(db_label)

    button_frame = ttk.Frame(mixer_frame)
    button_frame.grid(row=0, column=1, sticky="ne", padx=10, pady=10)

    open_temp_button = ttk.Button(button_frame, text="Session Audios", command=open_temp_directory)
    open_temp_button.pack(side="top", pady=5)

    equalizer_button = ttk.Button(button_frame, text="Equalizer", command=open_equalizer)
    equalizer_button.pack(side="top", pady=5)

    trim_button = ttk.Button(button_frame, text="Trim", command=open_trim_window)
    trim_button.pack(side="top", pady=5)

    check_for_updates()
    globals.window.mainloop()
