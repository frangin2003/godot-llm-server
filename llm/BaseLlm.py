from stt_utils import recognize_speech_from_audio_url
from image_utils import image_url_to_data_url
from abc import ABC, abstractmethod

class BaseLlm(ABC):
    def __init__(self, model_name, debug=False):
        self.model_name = model_name
        self.debug = debug
        self.llm = self.init_llm()

    def get_prompt_from_messages(self, data):
        prompt = self.initialize_prompt()
        for message in data['messages']:
            role = message['role']
            content = message['content']
            if isinstance(content, str):
                prompt = self.accumulate_prompt(prompt, self.get_role_prompt(role, content))
            elif isinstance(content, list):
                for item in content:
                    if item['type'] == 'text':
                        prompt = self.accumulate_prompt(prompt, self.get_role_prompt(role, item['text']))
                    elif item['type'] == 'speech_url':
                        prompt = self.accumulate_prompt(prompt, self.get_role_prompt_from_speech_url(role, item['speech_url']['url']))
                    elif item['type'] == 'image_url':
                        prompt = self.accumulate_prompt(prompt, self.get_role_prompt_from_image_url(role, item['image_url']['url']))
        prompt = self.accumulate_prompt(prompt, self.finalize_prompt())
        if self.debug:
            print(prompt)
        return prompt

    def get_role_prompt_from_speech_url(self, role, speech_url):
        return self.get_role_prompt(role, recognize_speech_from_audio_url(speech_url))

    def get_role_prompt_from_image_url(self, role, image_url):
        data_url = image_url_to_data_url(image_url)
        if data_url is None:
            return ""
        return self.get_role_prompt(role, data_url)

    def accumulate_prompt(self, prompt, new_prompt):
        if isinstance(prompt, list):
            prompt.extend(new_prompt)
        else:
            prompt += new_prompt
        return prompt

    @abstractmethod
    def initialize_prompt(self):
        pass

    @abstractmethod
    def finalize_prompt(self):
        pass

    @abstractmethod
    def get_role_prompt(self, role, prompt):
        pass

    @abstractmethod
    def get_stop_terms(self):
        pass

    @abstractmethod
    def init_llm(self):
        pass

