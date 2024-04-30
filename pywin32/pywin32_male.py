import win32com.client
import pythoncom
import time

def speak_text_and_save_to_file(text, filename):
    pythoncom.CoInitialize()  # Initialize the COM environment for the current thread
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    speaker.Voice = speaker.GetVoices().Item(0)
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    stream.Open(filename, 3)  # 3 = SSFMCreateForWrite
    speaker.AudioOutputStream = stream
    speaker.Speak(text)
    stream.Close()
    pythoncom.CoUninitialize()  # Uninitialize the COM environment for the current thread

# Example usage
# speak_text_and_save_to_file("Hello, this is a test of Microsoft's Speech API.", "test_speech.wav")
speak_text_and_save_to_file("As the sun dips below the horizon, the African savannah transforms into a nocturnal wonderland, alive with the symphony of nocturnal creatures. The gentle rustle of leaves whispers tales of ancient forests, where time stands still and nature reigns supreme. Behold the intricate dance of life, where every creature plays its part in the grand tapestry of existence.",
                            "pywin32_male.wav")
