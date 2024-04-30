import unittest
from unittest.mock import patch
from prompt_utils import get_llama3_prompt_from_messages, get_role_prompt, get_role_prompt_from_speech_url, get_role_prompt_from_image_url

class TestPromptUtils(unittest.TestCase):

    def setUp(self):
        self.sample_data = {
            'messages': [
                {'role': 'user', 'content': 'Hello, how are you?'},
                {'role': 'system', 'content': 'I am fine, thank you!'},
                {'role': 'user', 'content': [{'type': 'text', 'text': 'What is the weather today?'}]},
                {'role': 'user', 'content': [{'type': 'speech_url', 'speech_url': {'url': 'http://example.com/audio.mp3'}}]},
                {'role': 'user', 'content': [{'type': 'image_url', 'image_url': {'url': 'http://example.com/image.png'}}]}
            ]
        }

    def test_get_role_prompt(self):
        result = get_role_prompt('user', 'Hello, how are you?')
        expected = "<|start_header_id|>user<|end_header_id|>\nHello, how are you?<|eot_id|>"
        self.assertEqual(result, expected)

    @patch('prompt_utils.recognize_speech_from_audio_url')
    def test_get_role_prompt_from_speech_url(self, mock_recognize_speech_from_audio_url):
        mock_recognize_speech_from_audio_url.return_value = "Speech converted to text"
        result = get_role_prompt_from_speech_url('user', 'http://example.com/audio.mp3')
        expected = "<|start_header_id|>user<|end_header_id|>\nSpeech converted to text<|eot_id|>"
        self.assertEqual(result, expected)

    @patch('prompt_utils.image_url_to_data_url')
    def test_get_role_prompt_from_image_url(self, mock_image_url_to_data_url):
        mock_image_url_to_data_url.return_value = "data:image/png;base64,encodedstring"
        result = get_role_prompt_from_image_url('user', 'http://example.com/image.png')
        expected = "<|start_header_id|>user<|end_header_id|>\ndata:image/png;base64,encodedstring<|eot_id|>"
        self.assertEqual(result, expected)

    @patch('prompt_utils.recognize_speech_from_audio_url')
    @patch('prompt_utils.image_url_to_data_url')
    def test_get_llama3_prompt_from_messages(self, mock_image_url_to_data_url, mock_recognize_speech_from_audio_url):
        mock_recognize_speech_from_audio_url.return_value = "Speech converted to text"
        mock_image_url_to_data_url.return_value = "data:image/png;base64,encodedstring"

        expected_prompt = ("<|begin_of_text|>"
                           "<|start_header_id|>user<|end_header_id|>\nHello, how are you?<|eot_id|>"
                           "<|start_header_id|>system<|end_header_id|>\nI am fine, thank you!<|eot_id|>"
                           "<|start_header_id|>user<|end_header_id|>\nWhat is the weather today?<|eot_id|>"
                           "<|start_header_id|>user<|end_header_id|>\nSpeech converted to text<|eot_id|>"
                           "<|start_header_id|>user<|end_header_id|>\ndata:image/png;base64,encodedstring<|eot_id|>"
                           "<|start_header_id|>assistant<|end_header_id|>")

        result = get_llama3_prompt_from_messages(self.sample_data)
        self.assertEqual(result, expected_prompt)

if __name__ == '__main__':
    unittest.main()
