from pydub import AudioSegment
from pydub.playback import play
import win32com.client
import pythoncom
import time

def adjust_pitch_for_deeper_voice(audio_file, new_pitch=0.7):
    # Load audio file
    song = AudioSegment.from_file(audio_file)
    # Lower pitch
    octaves = new_pitch - 0.5
    new_sample_rate = int(song.frame_rate * (4.0 ** octaves))
    # Pitch shifted song is slightly slower; let's keep the same length
    deeper_voice = song._spawn(song.raw_data, overrides={'frame_rate': new_sample_rate})
    slowed_down_deeper_voice = deeper_voice.set_frame_rate(song.frame_rate)
    return slowed_down_deeper_voice


def speak_text_and_save_to_file(text, filename):
    pythoncom.CoInitialize()  # Initialize the COM environment for the current thread
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    temp_filename = "temp_" + filename
    stream.Open(temp_filename, 3)  # 3 = SSFMCreateForWrite
    speaker.AudioOutputStream = stream
    speaker.Speak(text)
    stream.Close()
    pythoncom.CoUninitialize()  # Uninitialize the COM environment for the current thread
    
    # Adjust pitch of the saved audio file while maintaining its length
    chipmunk_voice = adjust_pitch_for_deeper_voice(temp_filename)
    # Save the modified audio
    chipmunk_voice.export(filename, format="wav")
    # Optionally, play the modified audio
    # play(chipmunk_voice)

# Example usage
speak_text_and_save_to_file("As the sun dips below the horizon, the African savannah transforms into a nocturnal wonderland, alive with the symphony of nocturnal creatures. The gentle rustle of leaves whispers tales of ancient forests, where time stands still and nature reigns supreme. Behold the intricate dance of life, where every creature plays its part in the grand tapestry of existence.",
                            "pywin32_kid.wav")
