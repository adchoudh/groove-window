import tkinter as tk
from tkinter import ttk, messagebox
import globals
from audio_processing import (
    load_audio, play_all_audio, pause_audio, resume_audio,
    adjust_volume, save_project, load_project, export_project_as_mp3, detect_bpm
)
from trim_function import open_trim_window
import os
import subprocess
import sys
from pydub import AudioSegment
from track_timeline import (
    setup_track_timeline, toggle_cell, play_timeline, start_timeline_playback
)

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
            globals.update_total_length()  # Update total length when a track is reloaded
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

def move_cursor():
    try:
        target_second = float(globals.cursor_entry.get())
        max_duration = max(globals.track_durations)
        if target_second < 0 or target_second > max_duration:
            messagebox.showerror("Invalid Time", "Please enter a valid time within the track duration.")
            return
        globals.cursor_position = target_second
        print(f"Move Cursor: Setting cursor_position to {globals.cursor_position} seconds.")
        # Stop any current playback
        for channel in globals.channels:
            channel.stop()
        globals.playback_start_time = None
        # Update the current position display
        globals.update_current_playback_time()
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid number.")
    except Exception as e:
        messagebox.showerror("Move Cursor Error", f"An unexpected error occurred:\n{e}")
        print(f"Move Cursor Error: {e}")

def setup_main_window():
    globals.window = tk.Tk()
    globals.window.title("Groove Window")
    globals.window.geometry("1920x1080")

    # Configure grid rows and columns
    globals.window.grid_rowconfigure(0, weight=0)
    globals.window.grid_rowconfigure(1, weight=1)
    globals.window.grid_columnconfigure(0, weight=1)
    globals.window.grid_columnconfigure(1, weight=1)

    # Control Frame (at the top, spanning both columns)
    control_frame = ttk.Frame(globals.window)
    control_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")

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

    cursor_entry_label = ttk.Label(control_frame, text="Cursor Position (s):")
    cursor_entry_label.grid(row=0, column=8, padx=5)

    cursor_entry = ttk.Entry(control_frame, width=10)
    cursor_entry.grid(row=0, column=9, padx=5)
    cursor_entry.insert(0, "0")
    globals.cursor_entry = cursor_entry

    move_cursor_button = ttk.Button(control_frame, text="Move Cursor", command=move_cursor)
    move_cursor_button.grid(row=0, column=10, padx=5)

    current_time_label = ttk.Label(control_frame, text="Current Position: 0:00")
    current_time_label.grid(row=0, column=11, padx=10)
    globals.current_time_label = current_time_label

    total_length_label = ttk.Label(control_frame, text="Total Length: 0:00")
    total_length_label.grid(row=0, column=12, padx=10)
    globals.total_length_label = total_length_label

    timeline_play_button = ttk.Button(control_frame, text="Play Timeline", command=start_timeline_playback)
    timeline_play_button.grid(row=0, column=13, padx=10)

    # Left Frame
    left_frame = ttk.Frame(globals.window)
    left_frame.grid(row=1, column=0, sticky="nsew")
    left_frame.grid_rowconfigure(0, weight=1)
    left_frame.grid_rowconfigure(1, weight=1)
    left_frame.grid_columnconfigure(0, weight=1)

    track_frame = ttk.Frame(left_frame, padding="10")
    track_frame.grid(row=0, column=0, sticky="nsew")
    track_frame.grid_columnconfigure(0, weight=1)
    globals.track_labels = []
    globals.track_bpm_labels = [None] * 10

    for track in range(10):
        frame = ttk.Frame(track_frame)
        frame.grid(row=track, column=0, padx=10, pady=5, sticky="w")
        label = ttk.Label(frame, text=f"Track {track + 1}", width=40)
        label.pack(side="left")
        globals.track_labels.append(label)
        load_button = ttk.Button(frame, text="Load Audio", command=lambda t=track: load_audio(t))
        load_button.pack(side="left", padx=5)
        detect_bpm_button = ttk.Button(frame, text="Detect BPM", command=lambda t=track: detect_bpm(t))
        detect_bpm_button.pack(side="left", padx=5)

    mixer_frame = ttk.Frame(left_frame, padding="10")
    mixer_frame.grid(row=1, column=0, sticky="nsew")
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
        channel_frame.grid(row=row, column=column, padx=3, pady=3)  
        ttk.Label(channel_frame, text=f"Channel {i + 1}").pack()

        slider_meter_frame = ttk.Frame(channel_frame)
        slider_meter_frame.pack()

        mixer_slider = ttk.Scale(
            slider_meter_frame,
            orient="horizontal",
            length=75,  # Reduced slider length
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
            length=75,  # Reduced progress bar length
            mode="determinate",
            maximum=100
        )
        volume_meter.pack(pady=1)
        globals.volume_meters.append(volume_meter)

        db_label = ttk.Label(channel_frame, text="-inf dB")
        db_label.pack()
        globals.db_labels.append(db_label)

    def open_keyboard():
        from keyboard_window import open_keyboard_window
        open_keyboard_window()

    def open_drum_pad():
        from drumpad_window import open_drumpad_window
        open_drumpad_window()

    button_frame = ttk.Frame(mixer_frame)
    button_frame.grid(row=0, column=1, sticky="ne", padx=10, pady=10)

    # Button: Session Audios
    open_temp_button = ttk.Button(button_frame, text="Session Audios", command=open_temp_directory)
    open_temp_button.pack(side="top", pady=5)

    trim_button = ttk.Button(button_frame, text="Trim", command=open_trim_window)
    trim_button.pack(side="top", pady=5)

    equalizer_button = ttk.Button(button_frame, text="Equalizer", command=open_equalizer)
    equalizer_button.pack(side="top", pady=5)

    # Button: Keyboard
    keyboard_button = ttk.Button(button_frame, text="Keyboard", command=open_keyboard)
    keyboard_button.pack(side="top", pady=5)

    # Button: Drum Pad
    drum_pad_button = ttk.Button(button_frame, text="Drum Pad", command=open_drum_pad)
    drum_pad_button.pack(side="top", pady=5)

    # Button: Play Timeline
    play_timeline_button = ttk.Button(button_frame, text="Play Timeline", command=start_timeline_playback)
    play_timeline_button.pack(side="top", pady=5)

    timeline_frame = ttk.Frame(globals.window)
    timeline_frame.grid(row=1, column=1, sticky="nsew")
    timeline_frame.grid_rowconfigure(0, weight=1)
    timeline_frame.grid_columnconfigure(0, weight=1)
    setup_track_timeline(timeline_frame)

    globals.window.grid_rowconfigure(1, weight=1)
    globals.window.grid_columnconfigure(0, weight=1)
    globals.window.grid_columnconfigure(1, weight=1)

    globals.current_time_label = current_time_label
    globals.total_length_label = total_length_label

    check_for_updates()
    globals.update_current_playback_time()
    globals.window.mainloop()
