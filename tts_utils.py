import pythoncom
from pydub import AudioSegment
import winsound
import win32com.client
import io

voice_types = {
    "001": {
        "type": "male",
        "voice_id": 1,
        "pitch": 1.0,
        "octaves_multiplier": 1.0
    },
    "002": {
        "type": "female",
        "voice_id": 2,
        "pitch": 1.0,
        "octaves_multiplier": 1.0
    },
    "003": {
        "type": "chipmunk",
        "voice_id": None,
        "pitch": 0.7,
        "octaves_multiplier": 2.0
    },
    "004": {
        "type": "deepmale",
        "voice_id": None,
        "pitch": -0.6,
        "octaves_multiplier": 2.0
    },
    "005": {
        "type": "kid",
        "voice_id": None,
        "pitch": 0.2,
        "octaves_multiplier": 4.0
    },
    "006": {
        "type": "male",
        "voice_id": 0,
        "pitch": 1.0,
        "octaves_multiplier": 1.0
    },
    "007": {
        "type": "male2",
        "voice_id": 1,
        "pitch": -0.3,
        "octaves_multiplier": 2.0
    },
    "008": {
        "type": "oldfemale",
        "voice_id": 1,
        "pitch": -0.1,
        "octaves_multiplier": 10.0
    }
}

def adjust_pitch_and_octaves(audio_segment, new_pitch=1.0, octaves_multiplier=1.0):
    song = audio_segment
    octaves = new_pitch
    new_sample_rate = int(song.frame_rate * (octaves_multiplier ** octaves))
    deeper_voice = song._spawn(song.raw_data, overrides={'frame_rate': new_sample_rate})
    slowed_down_deeper_voice = deeper_voice.set_frame_rate(song.frame_rate)
    return slowed_down_deeper_voice


def speak_text(text, speaker_id="001", callback=None):
    print("Initializing COM...")
    pythoncom.CoInitialize()
    print("COM initialized")
    speaker = None
    stream = None
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        stream = win32com.client.Dispatch("SAPI.SpMemoryStream")
        
        voice_type = voice_types[speaker_id]["type"] if speaker_id in voice_types else voice_types["001"]["type"]
        print(f"The selected voice type is: {voice_type}")
        voice_id = voice_types[speaker_id]["voice_id"]
        pitch = voice_types[speaker_id]["pitch"]
        octaves_multiplier = voice_types[speaker_id]["octaves_multiplier"]
        
        # Add voice validation
        voices = speaker.GetVoices()
        if voice_id is not None and voice_id < voices.Count:
            speaker.Voice = voices.Item(voice_id)
        else:
            print(f"Warning: Voice ID {voice_id} not available, using default voice")
        
        # Set up format for 16-bit PCM WAV using SAPI constants
        # SAFT22kHz16BitMono = 22
        stream.Format.Type = 22
        
        speaker.AudioOutputStream = stream
        speaker.Speak(text)
        # Get raw audio data
        data = stream.GetData()
        
        # Define audio format parameters based on SAFT22kHz16BitMono
        channels = 1
        sample_rate = 22050  # 22kHz
        bits_per_sample = 16
        block_align = channels * (bits_per_sample // 8)
        avg_bytes_per_sec = sample_rate * block_align
        
        # Create WAV header
        wav_header = bytearray()
        # RIFF header
        wav_header.extend(b'RIFF')
        wav_header.extend((len(data) + 36).to_bytes(4, 'little'))  # File size - 8
        wav_header.extend(b'WAVE')
        # fmt chunk
        wav_header.extend(b'fmt ')
        wav_header.extend((16).to_bytes(4, 'little'))  # Chunk size
        wav_header.extend((1).to_bytes(2, 'little'))   # Audio format (PCM)
        wav_header.extend(channels.to_bytes(2, 'little'))
        wav_header.extend(sample_rate.to_bytes(4, 'little'))
        wav_header.extend(avg_bytes_per_sec.to_bytes(4, 'little'))
        wav_header.extend(block_align.to_bytes(2, 'little'))
        wav_header.extend(bits_per_sample.to_bytes(2, 'little'))
        # data chunk
        wav_header.extend(b'data')
        wav_header.extend(len(data).to_bytes(4, 'little'))
        
        # Combine header and data
        wav_data = io.BytesIO()
        wav_data.write(wav_header)
        wav_data.write(data)
        wav_data.seek(0)
        
        # Load audio from memory
        result_voice = AudioSegment.from_wav(wav_data)
        
        # Adjust pitch of the audio data
        result_voice = adjust_pitch_and_octaves(result_voice, pitch, octaves_multiplier)
        
        # Get the runtime of the sound
        runtime = len(result_voice) / 1000.0
        print(f"Runtime of the sound: {runtime:.2f} seconds")
        
        if callback:
            callback(runtime, speaker_id)
        
        print("Attempting to play audio with winsound...")
        # Export the final AudioSegment to an in-memory WAV byte stream
        wav_export_stream = io.BytesIO()
        result_voice.export(wav_export_stream, format="wav")
        wav_bytes_for_winsound = wav_export_stream.getvalue()
        
        # Play WAV bytes from memory. This is a blocking call.
        winsound.PlaySound(wav_bytes_for_winsound, winsound.SND_MEMORY | winsound.SND_NODEFAULT)
        print("Audio playback with winsound completed.")
            
    except Exception as e:
        print(f"Error in speak_text: {e}")
        import traceback
        traceback.print_exc()
    finally:
        speaker = None
        stream = None
        print("Uninitializing COM...")
        pythoncom.CoUninitialize()
        print("COM uninitialized")

def tts_async(text, speaker_id, callback=None):
    try:
        print("Attempting to speak new response...")
        speak_text(text, speaker_id, callback)
        print("Speaking complete.")
    except Exception as e:
        print(f"Error in tts_async: {e}")
        import traceback
        traceback.print_exc()