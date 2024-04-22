# https://support.microsoft.com/en-us/windows/appendix-a-supported-languages-and-voices-4486e345-7730-53da-fcfe-55cc64300f01
from pydub import AudioSegment
from pydub.playback import play
import win32com.client
import pythoncom
import time

def list_voices():
    pythoncom.CoInitialize()  # Initialize the COM environment for the current thread
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    for voice in speaker.GetVoices():
        print("ID:", voice.Id)
        print("Name:", voice.GetDescription())
    pythoncom.CoUninitialize()

def adjust_speed_and_add_grain(audio_file, speed=1.0, grain_level=0):
    # Load audio file
    song = AudioSegment.from_file(audio_file)
    # Slow down the audio to mimic an old man's speech speed
    slowed_song = song.speedup(playback_speed=speed)
    # Add grain to the audio to mimic the old man's voice texture
    grainy_voice = slowed_song + grain_level
    return grainy_voice

def speak_text_and_save_to_file(text, filename):
    pythoncom.CoInitialize()  # Initialize the COM environment for the current thread
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    # speaker.Voice = speaker.GetVoices().Item(0)
    speaker.Voice = speaker.GetVoices().Item(1)
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    # temp_filename = "temp_" + filename
    stream.Open(filename, 3)  # 3 = SSFMCreateForWrite
    speaker.AudioOutputStream = stream
    speaker.Speak(text)
    stream.Close()
    pythoncom.CoUninitialize()  # Uninitialize the COM environment for the current thread
    
    # Adjust speed and add grain to the saved audio file to mimic an old man's voice
    # old_man_voice = adjust_speed_and_add_grain(temp_filename)
    # Save the modified audio
    # old_man_voice.export(filename, format="wav")
    # Optionally, play the modified audio
    # play(old_man_voice)

# Example usage
speak_text_and_save_to_file("As the sun dips below the horizon, the African savannah transforms into a nocturnal wonderland, alive with the symphony of nocturnal creatures. The gentle rustle of leaves whispers tales of ancient forests, where time stands still and nature reigns supreme. Behold the intricate dance of life, where every creature plays its part in the grand tapestry of existence.", "african_savannah_night.wav")

from pydub import AudioSegment, effects
import librosa
import numpy as np
import soundfile as sf

def process_audio(audio_file, output_file, pitch_factor=1.0, adjust_pitch=False, normalize_audio=False, reduce_noise=True):
    """
    Process audio file to adjust pitch, normalize, and reduce noise.
    
    Parameters:
    - audio_file: Path to the input audio file.
    - output_file: Path where the processed audio will be saved.
    - pitch_factor: Factor to adjust the pitch. Values < 1 will lower the pitch.
    - normalize_audio: Whether to normalize the audio.
    - reduce_noise: Whether to perform noise reduction.
    """
    
    # Load the audio file
    y, sr = librosa.load(audio_file)
    
    # Noise reduction
    if reduce_noise:
        # Estimate the 'noise' part of the audio by averaging the first second
        noise_profile = np.mean(y[:sr], axis=0)
        y_reduced_noise = y - noise_profile
    else:
        y_reduced_noise = y

    # Adjust pitch
    if adjust_pitch:
        y_pitch_shifted = librosa.effects.pitch_shift(y=y_reduced_noise, sr=sr, n_steps=pitch_factor)
    else:
        y_pitch_shifted = y_reduced_noise
    

    # Save the intermediate processed file
    intermediate_file = 'temp_processed.wav'
    sf.write(intermediate_file, y_pitch_shifted, sr)

    # Normalize audio using PyDub (if needed)
    if normalize_audio:
        audio_segment = AudioSegment.from_file(intermediate_file)
        normalized_audio = effects.normalize(audio_segment)
        normalized_audio.export(output_file, format="wav")
    else:
        # Just save the processed file without normalization
        sf.write(output_file, y_pitch_shifted, sr)

# Example usage
process_audio('./african_savannah_night.wav', './better.wav', pitch_factor=-2)


list_voices()