from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from stt_utils import recognize_speech_from_audio_url
from image_utils import image_url_to_data_url

def get_gpt4_prompt_from_messages(data, debug=False):

    # prompt_array = [
    #     HumanMessage(content=[
    #         {"type": "text", "text": "Let's play a game. Think of a country and give me a clue. The clue must be specific enough that there is only one correct country. I will try pointing at the country on a map."},
    #     ]),
    #     SystemMessage(content=[{"type": "text", "text": "Alright, here's your clue: This country is renowned for being the birthplace of both the ancient Olympic Games and democracy. Where would you point on the map?"}]),
    #     # HumanMessage(content=[
    #     #     {"type": "text", "text": "Is it Greece?"},
    #     # ]),
    #     HumanMessage(content=[
    #         {"type": "image_url", "image_url": { "url" : data['messages'][1]['content'][1]['image']['url']} },
    #     ])
    # ]

    prompt_array = []

    for message in data['messages']:

        role = message['role']
        content = message['content']

        if isinstance(content, str):
            prompt_array.append(get_gpt4_role_text_message(role, content))
        elif isinstance(content, list):
            for item in content:
                if item['type'] == 'text':
                    message = get_gpt4_role_text_message(role, item['text'])
                    if message is not None:
                        prompt_array.append(message)
                elif item['type'] == 'speech_url':
                    message = get_gpt4_role_prompt_from_speech_url(role, item['speech_url']['url'])
                    if message is not None:
                        prompt_array.append(message)
                elif item['type'] == 'image_url':
                    message = get_gpt4_role_prompt_from_image_url(role, item['image_url']['url'])
                    if message is not None:
                        prompt_array.append(message)
    
    return prompt_array

def get_gpt4_role_text_message(role, prompt):
    if prompt is None:
        return None
    if role == "user":
        print('HumanMessage(content=[{"type": "text", "text": "' + prompt + '"}])')
        return HumanMessage(content=[{"type": "text", "text": prompt}])
    elif role == "system":
        print('SystemMessage(content=[{"type": "text", "text": "' + prompt + '"}])')
        return SystemMessage(content=[{"type": "text", "text": prompt}])
    else:
        print('AIMessage(content=[{"type": "text", "text": "' + prompt + '"}])')
        return AIMessage(content=[{"type": "text", "text": prompt}])

def get_gpt4_role_prompt_from_speech_url(role, speech_url):
    return get_gpt4_role_text_message(role, recognize_speech_from_audio_url(speech_url))

def get_gpt4_role_prompt_from_image_url(role, image_url):
    data_url = image_url_to_data_url(image_url)
    if data_url is None:
        return None
    if role == "user":
        print('HumanMessage(content=[{"type": "image_url", "image_url": { "url": "' + data_url + '"}}])')
        return HumanMessage(content=[{"type": "image_url", "image_url": { "url": data_url }}])
    elif role == "system":
        print('SystemMessage(content=[{"type": "image_url", "image_url": { "url": "' + data_url + '"}}])')
        return SystemMessage(content=[{"type": "image_url", "image_url": { "url": data_url }}])
    else:
        print('AIMessage(content=[{"type": "image_url", "image_url": { "url": "' + data_url + '"}}])')
        return AIMessage(content=[{"type": "image_url", "image_url": { "url": data_url }}])

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
