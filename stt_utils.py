import speech_recognition as sr
from io import BytesIO


# Function to recognize speech from audio URL
def recognize_speech_from_audio_url(audio_url):
    with open(audio_url, 'rb') as audio_file:
        audio_data = audio_file.read()
    return recognize_speech_from_audio_data(audio_data)

# Function to recognize speech from audio binary data
def recognize_speech_from_audio_data(audio_data):
    audio_file = BytesIO(audio_data)
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)  # read the entire audio file
    try:
        # for testing purposes, we're using the default API key
        # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Google Speech Recognition could not understand audio"
    except sr.RequestError as e:
        return f"Could not request results from Google Speech Recognition service; {e}"