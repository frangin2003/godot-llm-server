import os
import tempfile
import pythoncom
from pydub import AudioSegment
from pydub.playback import play
import win32com.client
import time

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

def adjust_pitch_and_octaves(audio_file, new_pitch=1.0, octaves_multiplier=1.0):
    # Load audio file
    song = AudioSegment.from_file(audio_file)
    # Lower pitch
    octaves = new_pitch
    new_sample_rate = int(song.frame_rate * (octaves_multiplier ** octaves))
    # Pitch shifted song is slightly slower; let's keep the same length
    deeper_voice = song._spawn(song.raw_data, overrides={'frame_rate': new_sample_rate})
    slowed_down_deeper_voice = deeper_voice.set_frame_rate(song.frame_rate)
    return slowed_down_deeper_voice


def speak_text(text, speaker_id="001", callback=None):
    if not text or not text.strip():
        print("Warning: Empty text received, skipping TTS")
        return

    pythoncom.CoInitialize()
    speaker = None
    stream = None
    temp_filename = None
    stream_opened = False
    
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        stream = win32com.client.Dispatch("SAPI.SpFileStream")

        voice_type = voice_types[speaker_id]["type"] if speaker_id in voice_types else voice_types["001"]["type"]
        print(f"The selected voice type is: {voice_type}")
        voice_id = voice_types[speaker_id]["voice_id"]
        pitch = voice_types[speaker_id]["pitch"]
        octaves_multiplier = voice_types[speaker_id]["octaves_multiplier"]
        
        # Add voice validation
        voices = speaker.GetVoices()
        if voice_id is not None and voice_id < voices.Count:
            speaker.Voice = voices.Item(voice_id)
        
        temp_dir = tempfile.gettempdir()
        temp_filename = os.path.join(temp_dir, f"temp_{voice_type}_{int(time.time())}.wav")
        
        # Ensure the temp directory exists
        os.makedirs(temp_dir, exist_ok=True)
        
        # Clean up any existing file
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except:
                temp_filename = os.path.join(temp_dir, f"temp_{voice_type}_{int(time.time())}_{os.getpid()}.wav")
        
        try:
            stream.Open(temp_filename, 3)
            stream_opened = True
            speaker.AudioOutputStream = stream
            speaker.Speak(text.strip())  # Ensure text is stripped
        except Exception as e:
            print(f"Error during speech synthesis: {e}")
            raise

        if stream_opened:
            stream.Close()
            stream = None
            stream_opened = False
        
        time.sleep(0.1)  # Small delay to ensure file is written

        if not os.path.exists(temp_filename):
            raise Exception(f"Failed to create audio file at {temp_filename}")

        result_voice = adjust_pitch_and_octaves(temp_filename, pitch, octaves_multiplier)
        runtime = len(result_voice) / 1000.0
        
        if callback:
            callback(runtime, speaker_id)
        play(result_voice)
            
    except Exception as e:
        print(f"Error in speak_text: {str(e)}")
        if hasattr(e, 'excepinfo'):
            print(f"Extended error info: {e.excepinfo}")
        raise
    finally:
        if stream_opened and stream:
            try:
                stream.Close()
            except:
                pass
        # Clean up temp file
        if temp_filename and os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except:
                pass
        # Force COM cleanup
        speaker = None
        stream = None
        pythoncom.CoUninitialize()

def tts_async(text, speaker_id, callback=None):
    print(f"tts_async: text = {text}, speaker_id = {speaker_id}")
    try:
        pythoncom.CoInitialize()
        try:
            print("Attempting to speak new response...")
            speak_text(text, speaker_id, callback)
            print("Speaking complete.")
        except Exception as e:
            print(f"Error in speak_text: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                print("Error uninitializing COM")
    except Exception as e:
        print(f"Error in tts_async: {e}")
        import traceback
        traceback.print_exc()