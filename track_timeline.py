import tkinter as tk
import globals
import pygame
import threading
from time import sleep
import io


ROWS = 10  # Number of tracks
COLUMNS = 5  # 16-second intervals
INTERVAL_DURATION = 16  # Each interval duration in seconds

# Initialize a grid state to keep track of active cells (True for active, False for inactive)
grid_state = [[{"active": False, "button": None} for _ in range(COLUMNS)] for _ in range(ROWS)]


def setup_track_timeline(window):
    """
    Sets up the 10x5 grid in the main window for track management.
    """
    timeline_frame = tk.Frame(window)
    timeline_frame.grid(row=10, column=1, rowspan=ROWS, columnspan=COLUMNS, padx=20, pady=20, sticky="nsew")

    for row in range(ROWS):
        for col in range(COLUMNS):
            cell_button = tk.Button(
                timeline_frame,
                bg="white",
                width=10,
                height=2,
                command=lambda r=row, c=col: toggle_cell(r, c)
            )
            cell_button.grid(row=row, column=col, padx=5, pady=5)
            # Store button reference in grid_state for easy toggling
            grid_state[row][col]["button"] = cell_button


def toggle_cell(row, col):
    """
    Toggles the state of a cell in the grid.
    """
    cell = grid_state[row][col]
    cell["active"] = not cell["active"]
    cell["button"].configure(bg="blue" if cell["active"] else "white")


def convert_audio_segment_to_pygame_sound(audio_segment):
    """
    Converts a pydub.AudioSegment to a pygame.mixer.Sound object.
    """
    audio_data = io.BytesIO()
    audio_segment.export(audio_data, format="wav")
    audio_data.seek(0)
    return pygame.mixer.Sound(audio_data)


def play_timeline():
    """
    Controls playback according to the grid state, playing the appropriate tracks for each interval.
    """
    for interval in range(COLUMNS):
        # Check which tracks are active for this interval
        active_tracks = [row for row in range(ROWS) if grid_state[row][interval]["active"]]

        # Stop any currently playing sounds
        for channel in globals.channels:
            channel.stop()

        # Start playing the active tracks for this interval
        for track_index in active_tracks:
            if globals.tracks[track_index]:  # Check if a track is loaded
                pygame_sound = convert_audio_segment_to_pygame_sound(globals.tracks[track_index])
                globals.channels[track_index].play(pygame_sound)

        # Wait for the interval duration before moving to the next
        sleep(INTERVAL_DURATION)


def start_timeline_playback():
    """
    Starts the timeline playback in a separate thread to avoid freezing the GUI.
    """
    playback_thread = threading.Thread(target=play_timeline)
    playback_thread.start()


def add_timeline_play_button(window):
    """
    Adds a button to the main window to start timeline-based playback.
    """
    timeline_play_button = tk.Button(window, text="Play Timeline", command=start_timeline_playback)
    timeline_play_button.grid(row=0, column=1, padx=10, pady=10)
