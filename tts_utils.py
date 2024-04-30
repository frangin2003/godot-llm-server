import pythoncom

def tts_async(speaker, response):
    pythoncom.CoInitialize()
    try:
        # Debugging output
        print("Attempting to stop any ongoing speech...")
        speaker.Speak("", 2)  # Attempt to stop any ongoing speech
        print("Attempting to speak new response...")
        speaker.Speak(response)
        print("Speaking complete.")
    except Exception as e:
        print(f"An error occurred in speak_async: {e}")
    finally:
        pythoncom.CoUninitialize()  # Clean up COM initialization
