import tkinter as tk
from tkinter import ttk, messagebox
from pydub import AudioSegment
from pydub.playback import play
import threading
import globals
import os


def open_trim_window():
    trim_window = tk.Toplevel()
    trim_window.title("Trim Audio")
    trim_window.geometry("400x300")

    selected_track = tk.StringVar(value="Track 1")
    start_time = tk.DoubleVar(value=0.0)
    end_time = tk.DoubleVar(value=0.0)

    ttk.Label(trim_window, text="Select Track to Trim:").pack(pady=5)
    track_options = [f"Track {i+1}" for i in range(10)]
    track_menu = ttk.OptionMenu(trim_window, selected_track, track_options[0], *track_options)
    track_menu.pack()

    ttk.Label(trim_window, text="Start Time (seconds):").pack(pady=5)
    start_entry = ttk.Entry(trim_window, textvariable=start_time)
    start_entry.pack()

    ttk.Label(trim_window, text="End Time (seconds):").pack(pady=5)
    end_entry = ttk.Entry(trim_window, textvariable=end_time)
    end_entry.pack()

    buttons_frame = ttk.Frame(trim_window)
    buttons_frame.pack(pady=10)

    preview_button = ttk.Button(buttons_frame, text="Preview Trim", command=lambda: preview_trim(selected_track.get(), start_time.get(), end_time.get()))
    preview_button.grid(row=0, column=0, padx=5)

    apply_button = ttk.Button(buttons_frame, text="Apply Trim", command=lambda: apply_trim(selected_track.get(), start_time.get(), end_time.get(), trim_window))
    apply_button.grid(row=0, column=1, padx=5)


def preview_trim(track_index_str, start, end):
    try:
        track_index = int(track_index_str.split()[1]) - 1
        if not globals.tracks[track_index]:
            messagebox.showerror("Error", f"No audio loaded in {track_index_str}.")
            return

        start_ms = start * 1000
        end_ms = end * 1000
        if start_ms >= end_ms:
            messagebox.showerror("Error", "Start time must be less than end time.")
            return

        original_audio = globals.tracks[track_index]
        if end_ms > len(original_audio):
            messagebox.showerror("Error", "End time exceeds track duration.")
            return

        trimmed_audio = original_audio[start_ms:end_ms]
        threading.Thread(target=play, args=(trimmed_audio,), daemon=True).start()

    except Exception as e:
        messagebox.showerror("Preview Error", f"Failed to preview trimmed audio:\n{e}")


def apply_trim(track_index_str, start, end, window):
    try:
        track_index = int(track_index_str.split()[1]) - 1
        if not globals.tracks[track_index]:
            messagebox.showerror("Error", f"No audio loaded in {track_index_str}.")
            return

        start_ms = start * 1000
        end_ms = end * 1000
        if start_ms >= end_ms:
            messagebox.showerror("Error", "Start time must be less than end time.")
            return

        original_audio = globals.tracks[track_index]
        if end_ms > len(original_audio):
            messagebox.showerror("Error", "End time exceeds track duration.")
            return

        trimmed_audio = original_audio[start_ms:end_ms]
        globals.tracks[track_index] = trimmed_audio
        globals.original_tracks[track_index] = trimmed_audio

        file_path = globals.track_file_paths[track_index]
        trimmed_audio.export(file_path, format=os.path.splitext(file_path)[1][1:])

        duration_seconds = trimmed_audio.duration_seconds
        globals.track_durations[track_index] = duration_seconds
        duration_formatted = format_duration(duration_seconds)
        filename = os.path.basename(file_path)
        globals.track_labels[track_index].config(text=f"{filename} ({duration_formatted})")

        globals.update_total_length()  # Update total length after trimming

        messagebox.showinfo("Trim Successful", f"{track_index_str} has been trimmed.")
        window.destroy()

    except Exception as e:
        messagebox.showerror("Trim Error", f"Failed to apply trim:\n{e}")


def format_duration(seconds):
    minutes = int(seconds) // 60
    seconds = int(seconds) % 60
    return f"{minutes}:{seconds:02d}"
