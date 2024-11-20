import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pydub import AudioSegment
import pygame
import time
import globals


def open_keyboard_window():
    root = tk.Toplevel()
    root.title("Keyboard Simulator")
    root.geometry("1300x1300") # We can adjust these for demo later

    script_dir = os.path.dirname(os.path.abspath(__file__))
    sounds_dir = os.path.join(script_dir, "Sounds_Piano")

    # Octaves and the notes for each
    octaves = {
        "Octave 3": [f"{note}3" for note in ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]],
        "Octave 4": [f"{note}4" for note in ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]],
        "Octave 5": [f"{note}5" for note in ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]],
    }

    # Key mappings for the computer keyboard
    key_map = {
        "a": "c",
        "w": "c#",
        "s": "d",
        "e": "d#",
        "d": "e",
        "f": "f",
        "t": "f#",
        "g": "g",
        "y": "g#",
        "h": "a",
        "u": "a#",
        "j": "b",
    }

    # File paths for all keys
    key_note_map = {}
    for octave, notes in octaves.items():
        for note in notes:
            file_path = os.path.join(sounds_dir, f"{note}.mp3")
            key_note_map[note] = file_path

    # We don't need this anymore cause it is integrated in the DAW already
    # pygame.mixer.init()

    # Load sounds 
    key_sounds = {}
    for note, file_path in key_note_map.items():
        if os.path.exists(file_path):
            key_sounds[note] = pygame.mixer.Sound(file_path)
        else:
            print(f"Warning: Sound file for {note} not found at {file_path}")



## GUI Stuff
    is_recording = False
    recorded_notes = []
    start_time = 0
    velocity_sliders = {}
    timer_update = None  

    velocity_frame = tk.Frame(root)
    velocity_frame.pack(pady=10)

    keys_frame = tk.Frame(root)
    keys_frame.pack(pady=20)

    # Play sound function
    def play_sound(note):
        sound = key_sounds.get(note)
        slider = velocity_sliders.get(note)
        if slider:
            velocity = slider.get()
        else:
            velocity = 64  # Default velocity (we can change later to whatever it should be)

        if sound:
            volume = velocity / 127.0
            sound.set_volume(volume)
            sound.play()

        if is_recording:
            timestamp = int((time.time() - start_time) * 1000)
            recorded_notes.append((key_note_map[note], velocity, timestamp))
            print(f"Recorded: {note} at {timestamp} ms with velocity {velocity}") # Print in terminal for testing

    # Function to start recording
    def start_recording():
        nonlocal is_recording, start_time, recorded_notes
        if is_recording:
            return  # Duplicate press
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
                root.after_cancel(timer_update)
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
            timer_update = root.after(500, update_timer) # Schedules the next update after 500 milliseconds
        else:
            timer_label.config(text="Recording Time: 0:00")

    # Function to save the recording
    # Automatically opens the Session Audios folder now
    def save_audio():
        if not recorded_notes:
            messagebox.showwarning("No Recording", "No notes have been recorded.")
            return

        max_timestamp = max(timestamp for _, _, timestamp in recorded_notes)
        output_duration = max_timestamp + 1000  # Add 1 second buffer at the end

        output_audio = AudioSegment.silent(duration=output_duration)

        for note_file, velocity, timestamp in recorded_notes:
            if os.path.exists(note_file):
                note_audio = AudioSegment.from_file(note_file)
                gain = -20 + (velocity * 20 / 127)
                adjusted_audio = note_audio.apply_gain(gain)
                output_audio = output_audio.overlay(adjusted_audio, position=timestamp)
            else:
                print(f"Note file {note_file} not found.")


        # Enter a filename function
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

            # Check in case the same name already exists
            if os.path.exists(file_path):
                overwrite = messagebox.askyesno("Overwrite File", f"A file named '{os.path.basename(file_path)}' already exists. Do you want to overwrite it?")
                if not overwrite:
                    return

            # Make it the proper format to be compatible with the DAW
            output_audio.export(file_path, format="wav", parameters=["-ar", "44100", "-ac", "2"])

            messagebox.showinfo("Recording Saved",
                                f"Recording saved as '{os.path.basename(file_path)}' in the Session Audios folder.\n\n"
                                "You can now load this file into your project using the 'Load Audio' button next to each track.")



    # Update keys and velocity sliders based on selected octave
    def update_keys(octave):
        for widget in keys_frame.winfo_children():
            widget.destroy()

        for widget in velocity_frame.winfo_children():
            widget.destroy()

        velocity_sliders.clear()

        tk.Label(velocity_frame, text="Velocity Controls", font=("Arial", 12, "bold")).pack()

        # Sliders updated when the octave is changed
        for note in octaves[octave]:
            frame = tk.Frame(velocity_frame)
            frame.pack(side=tk.LEFT, padx=5)
            tk.Label(frame, text=note.upper()).pack()
            slider = tk.Scale(frame, from_=0, to=127, orient=tk.VERTICAL)
            slider.set(64) 
            slider.pack()
            velocity_sliders[note] = slider

        # Keys updated when the octave is changed
        for note in octaves[octave]:
            btn = tk.Button(keys_frame, text=note.upper(), width=5, height=2, command=lambda n=note: play_sound(n))
            btn.pack(side=tk.LEFT, padx=5)





    # Function to play note from computer keyboard key press
    def play_note_from_key(event):
        key = event.char.lower()
        selected_octave = octave_dropdown.get()
        if key in key_map:
            note_base = key_map[key]
            note = f"{note_base}{selected_octave[-1]}"
            if note in key_sounds:
                play_sound(note)



    # Dropdown for octave selection
    selected_octave = tk.StringVar(value="Octave 3")
    octave_dropdown = ttk.Combobox(root, values=list(octaves.keys()), state="readonly", textvariable=selected_octave)
    octave_dropdown.pack(pady=10)
    octave_dropdown.bind("<<ComboboxSelected>>", lambda e: update_keys(selected_octave.get()))

    # Default octave (we can change this later)
    update_keys("Octave 3")

    # Bind keyboard keys to play notes
    root.bind("<KeyPress>", play_note_from_key)



    timer_label = tk.Label(root, text="Recording Time: 0:00", font=("Arial", 12))
    timer_label.pack(pady=10)


    tk.Button(root, text="Start Recording", command=start_recording).pack(pady=10)
    tk.Button(root, text="Stop Recording", command=stop_recording).pack(pady=10)
    tk.Button(root, text="Save Audio", command=save_audio).pack(pady=10)

    def on_close():
        # We don't need this anymore cause it is integrated in the DAW already
        # pygame.mixer.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
