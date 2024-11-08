import pygame
import tkinter as tk
import os
import tempfile

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

last_mod_times = [None] * 10

TEMP_DIR = os.path.join(tempfile.gettempdir(), "Session Audios")

track_durations = [0.0] * 10 

def setup_temp_dir():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
