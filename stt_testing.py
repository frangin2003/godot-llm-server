# Assuming the recognize_speech_from_audio_url function is defined in stt_utils.py

import stt_utils

def test_recognize_speech_from_audio_url():
    audio_url = "C:/Users/charles/Documents/__PROJECTS/sram-remaster/recorded_audio.wav"
    result = stt_utils.recognize_speech_from_audio_url(audio_url)
    print("Recognition Result:", result)

if __name__ == "__main__":
    test_recognize_speech_from_audio_url()