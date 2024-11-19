import pygame
import tkinter as tk
import os
import tempfile
import time

pygame.mixer.init()
pygame.mixer.set_num_channels(10)

tracks = [None] * 10
channels = [pygame.mixer.Channel(i) for i in range(10)]
paused_states = [False] * 10
original_tracks = [None] * 10
track_file_paths = [None] * 10
volume_levels = [1.0] * 10
bpm_var = None

window = None
track_labels = []
mixer_sliders = []
volume_meters = []
db_labels = []

# Globals for BPM detection
track_bpm_labels = [None] * 10  # Placeholder for BPM label widgets, one for each track

last_mod_times = [None] * 10

TEMP_DIR = os.path.join(tempfile.gettempdir(), "Session Audios")

track_durations = [0.0] * 10

# Global variables for cursor management
cursor_position = 0.0  # in seconds
playback_start_time = None  # timestamp when playback starts
current_playback_time = 0.0  # in seconds

total_length_label = None
current_time_label = None  # For dynamic cursor display

# Reference to cursor_entry widget
cursor_entry = None


def setup_temp_dir():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)


def format_duration(seconds):
    minutes = int(seconds) // 60
    seconds = int(seconds) % 60
    return f"{minutes}:{seconds:02d}"


def update_total_length():
    if track_durations:
        max_duration = max(track_durations)
    else:
        max_duration = 0.0
    if total_length_label:
        total_length_label.config(text=f"Total Length: {format_duration(max_duration)}")


def update_current_playback_time():
    global current_playback_time
    if playback_start_time:
        elapsed = time.time() - playback_start_time
        current_playback_time = cursor_position + elapsed
        if current_time_label:
            current_time_label.config(text=f"Current Position: {format_duration(current_playback_time)}")
        # Schedule next update
        window.after(500, update_current_playback_time)
    else:
        if current_time_label:
            current_time_label.config(text=f"Current Position: {format_duration(cursor_position)}")
