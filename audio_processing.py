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
    for i, track in enumerate(globals.tracks):
        if track:
            sound = convert_to_pygame_sound(track)
            globals.channels[i].stop()
            globals.channels[i].play(sound)
            globals.channels[i].set_volume(globals.volume_levels[i])
            globals.paused_states[i] = False
    start_volume_meter_updates()

def pause_audio():
    for i, channel in enumerate(globals.channels):
        if channel.get_busy():
            channel.pause()
            globals.paused_states[i] = True

def resume_audio():
    for i, channel in enumerate(globals.channels):
        if globals.paused_states[i]:
            channel.unpause()
            globals.paused_states[i] = False

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
        except Exception as e:
            messagebox.showerror("Load Project", f"Failed to load project:\n{e}")

def export_project_as_mp3():
    mixed_audio = None
    for i, track in enumerate(globals.tracks):
        if track:
            volume_level = globals.volume_levels[i]
            gain_db = 20 * math.log10(volume_level) if volume_level > 0 else -float('inf')
            adjusted_track = track.apply_gain(gain_db)
            if mixed_audio is None:
                mixed_audio = adjusted_track
            else:
                mixed_audio = mixed_audio.overlay(adjusted_track)
    if mixed_audio:
        file_path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3 Files", "*.mp3")])
        if file_path:
            mixed_audio.export(file_path, format="mp3")
            messagebox.showinfo("Export Project", "Project exported successfully!")
    else:
        messagebox.showwarning("Export Project", "No tracks loaded to export.")
