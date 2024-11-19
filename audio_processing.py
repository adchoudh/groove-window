import os
import io
import math
import json
import pygame
from pydub import AudioSegment
from time import sleep
from tkinter import filedialog, messagebox
import threading
import globals
import shutil
import librosa
import time
from track_timeline import grid_state, ROWS, COLUMNS, INTERVAL_DURATION

def detect_bpm(track_index):
    file_path = globals.track_file_paths[track_index]
    if file_path:
        try:
            y, sr = librosa.load(file_path)

            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            bpm = round(float(tempo))

            messagebox.showinfo(title="BPM Detection", message=f"Track {track_index + 1} BPM: {bpm}")
            return bpm
        except Exception as e:
            print(f"Error detecting BPM for track {track_index + 1}: {e}")
            messagebox.showerror(title="BPM Detection Error", message=f"Could not detect BPM for Track {track_index + 1}.")
            return None
    else:
        messagebox.showwarning(title="No File Loaded", message=f"No audio file loaded in Track {track_index + 1}.")
        return None

def load_audio(track_index, file_path=None):
    if not file_path:
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3")])
        if not file_path:
            return
        dest_filename = f"track_{track_index + 1}_{os.path.basename(file_path)}"
        dest_path = os.path.join(globals.TEMP_DIR, dest_filename)
        shutil.copy2(file_path, dest_path)
    else:
        dest_path = file_path
    try:
        audio = AudioSegment.from_file(dest_path)
        globals.original_tracks[track_index] = audio
        globals.tracks[track_index] = audio
        globals.track_file_paths[track_index] = dest_path

        duration_seconds = audio.duration_seconds
        globals.track_durations[track_index] = duration_seconds

        filename = os.path.basename(dest_path)
        duration_formatted = format_duration(duration_seconds)
        globals.track_labels[track_index].config(text=f"{filename} ({duration_formatted})")

        globals.last_mod_times[track_index] = os.path.getmtime(dest_path)
        globals.update_total_length()  # Update total length when a new track is loaded
    except Exception as e:
        messagebox.showerror("Load Audio", f"Failed to load audio file:\n{e}")

def format_duration(seconds):
    minutes = int(seconds) // 60
    seconds = int(seconds) % 60
    return f"{minutes}:{seconds:02d}"

def change_speed(sound, speed=1.0):
    new_sound = sound._spawn(sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * speed)})
    return new_sound.set_frame_rate(44100)

def apply_bpm_change():
    current_bpm = globals.bpm_var.get()
    speed_ratio = current_bpm / 120.0
    for i, original_track in enumerate(globals.original_tracks):
        if original_track:
            globals.tracks[i] = change_speed(original_track, speed_ratio)

def convert_to_pygame_sound(audio_segment):
    wav_io = io.BytesIO()
    audio_segment.export(wav_io, format="wav")
    wav_io.seek(0)
    return pygame.mixer.Sound(wav_io)

def update_volume_meters():
    while any(channel.get_busy() for channel in globals.channels):
        for i, track in enumerate(globals.tracks):
            if track and globals.channels[i].get_busy():
                rms = track.rms
                current_volume = globals.volume_levels[i]
                normalized_rms = min(rms / 1000, 1.0)
                effective_rms = normalized_rms * current_volume
                globals.volume_meters[i]['value'] = effective_rms * 100
                current_db = calculate_db(effective_rms * 1000)
                if current_db == -float('inf'):
                    globals.db_labels[i].config(text="-∞ dB")
                else:
                    globals.db_labels[i].config(text=f"{int(current_db)} dB")
        globals.window.update()
        sleep(0.1)

def calculate_db(rms):
    if rms == 0:
        return -float('inf')
    return 20 * math.log10(rms / 1000)

def start_volume_meter_updates():
    meter_thread = threading.Thread(target=update_volume_meters)
    meter_thread.daemon = True
    meter_thread.start()

def play_all_audio():
    apply_bpm_change()
    globals.playback_start_time = time.time()
    cursor_ms = globals.cursor_position * 1000  # Convert cursor position to milliseconds
    for i, track in enumerate(globals.tracks):
        if track:
            if cursor_ms >= len(track):
                continue  # Skip if cursor position is beyond track length
            # Trim the track to start from cursor_position
            track_to_play = track[cursor_ms:]
            sound = convert_to_pygame_sound(track_to_play)
            globals.channels[i].stop()
            globals.channels[i].play(sound)
            globals.channels[i].set_volume(globals.volume_levels[i])
            globals.paused_states[i] = False
    start_volume_meter_updates()
    globals.update_current_playback_time()

def pause_audio():
    for i, channel in enumerate(globals.channels):
        if channel.get_busy():
            channel.pause()
            globals.paused_states[i] = True
    if globals.playback_start_time:
        globals.paused_time = time.time() - globals.playback_start_time
    globals.playback_start_time = None  # Stop updating current playback time

def resume_audio():
    if globals.paused_time:
        globals.cursor_position += globals.paused_time
        globals.paused_time = None
    for i, channel in enumerate(globals.channels):
        if globals.paused_states[i]:
            channel.unpause()
            globals.paused_states[i] = False
    globals.playback_start_time = time.time()  # Resume updating current playback time
    globals.update_current_playback_time()

def adjust_volume(channel_index, volume):
    volume = float(volume)
    globals.volume_levels[channel_index] = volume
    globals.channels[channel_index].set_volume(volume)

def save_project():
    project_data = {
        "tracks": [],
        "bpm": globals.bpm_var.get(),
        "volume_levels": globals.volume_levels
    }
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if file_path:
        project_dir = os.path.splitext(file_path)[0]
        try:
            if not os.path.exists(project_dir):
                os.makedirs(project_dir)
            session_audios_src = globals.TEMP_DIR
            session_audios_dst = os.path.join(project_dir, "session_audios")
            if os.path.exists(session_audios_dst):
                shutil.rmtree(session_audios_dst)
            shutil.copytree(session_audios_src, session_audios_dst)
            for track_path in globals.track_file_paths:
                if track_path:
                    rel_path = os.path.relpath(track_path, session_audios_src)
                    project_data["tracks"].append(rel_path)
                else:
                    project_data["tracks"].append(None)
            json_file_path = os.path.join(project_dir, os.path.basename(file_path))
            with open(json_file_path, "w") as f:
                json.dump(project_data, f)
            messagebox.showinfo("Save Project", "Project saved successfully!")
        except Exception as e:
            messagebox.showerror("Save Project", f"Failed to save project:\n{e}")

def load_project():
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if file_path:
        project_dir = os.path.dirname(file_path)
        try:
            with open(file_path, "r") as f:
                project_data = json.load(f)
            session_audios_src = os.path.join(project_dir, "session_audios")
            session_audios_dst = globals.TEMP_DIR
            if os.path.exists(session_audios_dst):
                shutil.rmtree(session_audios_dst)
            shutil.copytree(session_audios_src, session_audios_dst)
            for i, rel_track_path in enumerate(project_data["tracks"]):
                if rel_track_path:
                    track_path = os.path.join(session_audios_dst, rel_track_path)
                    load_audio(i, file_path=track_path)
                else:
                    globals.track_file_paths[i] = None
                    globals.original_tracks[i] = None
                    globals.tracks[i] = None
                    globals.track_labels[i].config(text=f"Track {i + 1}")
            globals.bpm_var.set(project_data["bpm"])
            for i, volume in enumerate(project_data["volume_levels"]):
                globals.volume_levels[i] = volume
                globals.mixer_sliders[i].set(volume)
                globals.channels[i].set_volume(volume)
            messagebox.showinfo("Load Project", "Project loaded successfully!")
            globals.update_total_length()
        except Exception as e:
            messagebox.showerror("Load Project", f"Failed to load project:\n{e}")

def export_project_as_mp3():
    total_duration_ms = INTERVAL_DURATION * COLUMNS * 1000  # Total duration in milliseconds
    final_audio = AudioSegment.silent(duration=total_duration_ms)  # Initialize final audio with silence

    for row in range(ROWS):
        track = globals.tracks[row]
        if track:
            # Adjust volume according to the volume slider
            volume_level = globals.volume_levels[row]
            gain_db = 20 * math.log10(volume_level) if volume_level > 0 else -float('inf')
            adjusted_track = track.apply_gain(gain_db)

            # For each interval in the timeline
            for col in range(COLUMNS):
                cell = grid_state[row][col]
                if cell["active"]:
                    start_time_ms = col * INTERVAL_DURATION * 1000  # Start time of the interval
                    segment_duration_ms = INTERVAL_DURATION * 1000   # Duration of the interval

                    # Extract the segment from the beginning of the track
                    segment = adjusted_track[:segment_duration_ms]

                    # Pad the segment with silence if it's shorter than the interval
                    if len(segment) < segment_duration_ms:
                        segment += AudioSegment.silent(duration=(segment_duration_ms - len(segment)))

                    # Overlay the segment onto the final audio at the correct position
                    final_audio = final_audio.overlay(segment, position=start_time_ms)

    if final_audio:
        file_path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3 Files", "*.mp3")])
        if file_path:
            final_audio.export(file_path, format="mp3")
            messagebox.showinfo("Export Project", "Project exported successfully!")
    else:
        messagebox.showwarning("Export Project", "No tracks loaded to export.")

