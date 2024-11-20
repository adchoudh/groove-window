import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pydub import AudioSegment
import pygame
import time
import os
import globals

def open_drumpad_window():
    # Don't need to initialize pygame.mixer here if it's already initialized in globals.py
    # pygame.mixer.init()

    # Map sound paths to the sounds for the drum
    hi_hat_sounds = {
        "CHAIN": "Sounds_Drumpad/hihat/HI HAT - CHAIN.wav",
        "CHROME": "Sounds_Drumpad/hihat/HI HAT - CHROME.wav",
        "FLEXX": "Sounds_Drumpad/hihat/HI HAT - FLEXX.wav",
        "MONEYBAGG": "Sounds_Drumpad/hihat/HI HAT - MONEYBAGG.wav",
        "ZAY": "Sounds_Drumpad/hihat/HI HAT - ZAY.wav",
    }

    snare_sounds = {
        "88": "Sounds_Drumpad/snare/SNARE - 88.wav",
        "CLEAN": "Sounds_Drumpad/snare/SNARE - CLEAN.wav",
        "DARK": "Sounds_Drumpad/snare/SNARE - DARK.wav",
        "HEAVY": "Sounds_Drumpad/snare/SNARE - HEAVY.wav",
        "SANGUINE": "Sounds_Drumpad/snare/SNARE - SANGUINE.wav",
    }

    kick_sounds = {
        "AMP": "Sounds_Drumpad/kick/KICK - AMP.wav",
        "DRIZZY": "Sounds_Drumpad/kick/KICK - DRIZZY.wav",
        "DRONE": "Sounds_Drumpad/kick/KICK - DRONE.wav",
        "SAVE ME": "Sounds_Drumpad/kick/KICK - SAVE ME.wav",
        "SOUTHSIDE": "Sounds_Drumpad/kick/KICK - SOUTHSIDE.wav",
    }

    open_hat_sounds = {
        "CHARGE": "Sounds_Drumpad/openhat/OPEN HAT - CHARGE.wav",
        "COOLER": "Sounds_Drumpad/openhat/OPEN HAT - COOLER.wav",
        "HYPER": "Sounds_Drumpad/openhat/OPEN HAT - HYPER.wav",
        "RITA": "Sounds_Drumpad/openhat/OPEN HAT - RITA.wav",
        "SIMPLE": "Sounds_Drumpad/openhat/OPEN HAT - SIMPLE.wav",
    }

    is_recording = False
    recorded_notes = []
    start_time = 0
    timer_update = None 

    # Function to play a sound 
    def play_sound(selected_option, sound_mapping):
        nonlocal is_recording, recorded_notes, start_time
        if selected_option and selected_option != "Select a sound":
            sound_path = sound_mapping.get(selected_option)
            if sound_path:
                try:
                    pygame.mixer.Sound(sound_path).play()
                    if is_recording:
                        timestamp = int((time.time() - start_time) * 1000)
                        recorded_notes.append((sound_path, timestamp))
                        print(f"Recorded: {selected_option} at {timestamp} ms")
                except pygame.error as e:
                    print(f"Error playing sound: {e}")
            else:
                print(f"Sound file for {selected_option} not found.")
        else:
            print("No sound selected.")

    # Function to start recording
    def start_recording():
        nonlocal is_recording, start_time, recorded_notes
        if is_recording:
            return  
        is_recording = True
        recorded_notes = []
        start_time = time.time()
        print("Recording started")
        update_timer()  # Start the stopwatch

    # Function to stop recording
    def stop_recording():
        nonlocal is_recording, timer_update
        if is_recording:
            is_recording = False
            print("Recording stopped")
            if timer_update:
                window.after_cancel(timer_update)
                timer_update = None
            timer_label.config(text="Recording Time: 0:00")

    # Function to update the timer
    def update_timer():
        nonlocal timer_update
        if is_recording:
            elapsed_time = time.time() - start_time
            minutes = int(elapsed_time) // 60
            seconds = int(elapsed_time) % 60
            timer_label.config(text=f"Recording Time: {minutes}:{seconds:02d}")
            timer_update = window.after(500, update_timer)
        else:
            timer_label.config(text="Recording Time: 0:00")

    # Function to save the recording
    def save_audio():
        if not recorded_notes:
            messagebox.showwarning("No Recording", "No sounds have been recorded.")
            return

        max_timestamp = max(timestamp for _, timestamp in recorded_notes)
        output_duration = max_timestamp + 1000 

        output_audio = AudioSegment.silent(duration=output_duration)

        for sound_path, timestamp in recorded_notes:
            if os.path.exists(sound_path):
                sound = AudioSegment.from_file(sound_path)
                output_audio = output_audio.overlay(sound, position=timestamp)
            else:
                print(f"Sound file {sound_path} not found.")

        # Ask user to enter a filename
        file_name = filedialog.asksaveasfilename(
            initialdir=globals.TEMP_DIR,
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav")],
            title="Save Recording As"
        )

        if file_name:
            if not file_name.lower().endswith(".wav"):
                file_name += ".wav"

            file_path = file_name

            # Check if a file with the same name already exists
            if os.path.exists(file_path):
                overwrite = messagebox.askyesno("Overwrite File", f"A file named '{os.path.basename(file_path)}' already exists. Do you want to overwrite it?")
                if not overwrite:
                    return

            # Ensure standard format
            output_audio.export(file_path, format="wav", parameters=["-ar", "44100", "-ac", "2"])

            messagebox.showinfo("Recording Saved",
                                f"Recording saved as '{os.path.basename(file_path)}' in the Session Audios folder.\n\n"
                                "You can now load this file into your project using the 'Load Audio' button.")

    ## GUI setup
    window = tk.Toplevel()
    window.title("Drum Pad Recorder")
    window.geometry("800x800")

    # Create virtual drum pads
    def create_drumpad(frame, drumpad_number, label_text, sound_mapping):
        selected_option = tk.StringVar(value="Select a sound")
        label = tk.Label(frame, text=f"Drumpad {drumpad_number}: {label_text}", font=("Arial", 14, "bold"))
        label.pack(pady=(10, 5))
        dropdown = ttk.Combobox(frame, values=list(sound_mapping.keys()), state="readonly", textvariable=selected_option, font=("Arial", 12))
        dropdown.pack(pady=(0, 10))
        play_button = tk.Button(frame, text="Select and Play Sound", command=lambda: play_sound(selected_option.get(), sound_mapping))
        play_button.pack(pady=(0, 10))
        return selected_option

    frame = tk.Frame(window)
    frame.pack(pady=20)

    selected_hi_hat = create_drumpad(frame, 1, "Hi Hat", hi_hat_sounds)
    selected_snare = create_drumpad(frame, 2, "Snare", snare_sounds)
    selected_kick = create_drumpad(frame, 3, "Kick", kick_sounds)
    selected_open_hat = create_drumpad(frame, 4, "Open Hat", open_hat_sounds)

    # Virtual drum pads
    virtual_frame = tk.Frame(window)
    virtual_frame.pack(pady=20)

    tk.Button(virtual_frame, text="Hi Hat", command=lambda: play_sound(selected_hi_hat.get(), hi_hat_sounds)).pack(side=tk.LEFT, padx=10)
    tk.Button(virtual_frame, text="Snare", command=lambda: play_sound(selected_snare.get(), snare_sounds)).pack(side=tk.LEFT, padx=10)
    tk.Button(virtual_frame, text="Kick", command=lambda: play_sound(selected_kick.get(), kick_sounds)).pack(side=tk.LEFT, padx=10)
    tk.Button(virtual_frame, text="Open Hat", command=lambda: play_sound(selected_open_hat.get(), open_hat_sounds)).pack(side=tk.LEFT, padx=10)

    # Recording controls
    recording_frame = tk.Frame(window)
    recording_frame.pack(pady=20)

    tk.Button(recording_frame, text="Start Recording", command=start_recording).pack(side=tk.LEFT, padx=10)
    tk.Button(recording_frame, text="Stop Recording", command=stop_recording).pack(side=tk.LEFT, padx=10)
    tk.Button(recording_frame, text="Save Recording", command=save_audio).pack(side=tk.LEFT, padx=10)

    # Stopwatch 
    timer_label = tk.Label(window, text="Recording Time: 0:00", font=("Arial", 12))
    timer_label.pack(pady=10)

    # Keyboard pressing logic
    def on_key_press(event):
        key_to_pad = {
            "1": (selected_hi_hat, hi_hat_sounds),
            "2": (selected_snare, snare_sounds),
            "3": (selected_kick, kick_sounds),
            "4": (selected_open_hat, open_hat_sounds),
        }
        if event.char in key_to_pad:
            selected_option, sound_mapping = key_to_pad[event.char]
            play_sound(selected_option.get(), sound_mapping)

    window.bind("<KeyPress>", on_key_press)

    def on_close():
        # Don't need to quit the mixer here
        # pygame.mixer.quit()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_close)
