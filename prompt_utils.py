from stt_utils import recognize_speech_from_audio_url
from image_utils import image_url_to_data_url

def get_llama3_prompt_from_messages(data, debug=False):

    prompt = "<|begin_of_text|>"

    for message in data['messages']:

        role = message['role']
        content = message['content']

        if isinstance(content, str):
            prompt += get_role_prompt(role, content)
        elif isinstance(content, list):
            for item in content:
                if item['type'] == 'text':
                    prompt += get_role_prompt(role, item['text'])
                elif item['type'] == 'speech_url':
                    prompt += get_role_prompt_from_speech_url(role, item['speech_url']['url'])
                elif item['type'] == 'image_url':
                    prompt += get_role_prompt_from_image_url(role, item['image_url']['url'])
    
    prompt += "<|start_header_id|>assistant<|end_header_id|>"
    
    if debug:
        print(prompt)
    return prompt

def get_role_prompt(role, prompt):
    return f"<|start_header_id|>{role}<|end_header_id|>\n{prompt}<|eot_id|>"

def get_role_prompt_from_speech_url(role, speech_url):
    return get_role_prompt(role, recognize_speech_from_audio_url(speech_url))

def get_role_prompt_from_image_url(role, image_url):
    return get_role_prompt(role, image_url_to_data_url(image_url))
