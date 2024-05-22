from llm.OpenAILlm import OpenAILlm
from llm.Llama3Llm import Llama3Llm
from llm.Phi3ChatMLLlm import Phi3ChatMLLlm
from llm.MistralChatMLLlm import MistralChatMLLlm

def create_llm_instance(model_name, debug=False):
    if model_name in ["gpt4", "gpt4-turbo", "gpt4o"]:
        return OpenAILlm(model_name, debug)
    elif model_name in ["llama3"]:
        return Llama3Llm(model_name, debug)
    elif model_name in ["phi3"]:
        return Phi3ChatMLLlm(model_name, debug)
    elif model_name in ["mistral"]:
        return MistralChatMLLlm(model_name, debug)
    else:
        raise ValueError(f"Unknown model name: {model_name}")

