from llm.OpenAILlm import OpenAILlm
from llm.Llama3Llm import Llama3Llm
from llm.Phi3ChatMLLlm import Phi3ChatMLLlm
from llm.MistralChatMLLlm import MistralChatMLLlm

def create_llm_instance(model_name, debug=False):
    llm_instance = None
    if model_name in ["gpt4", "gpt4-turbo", "gpt4o"]:
        llm_instance = OpenAILlm(model_name, debug)
    elif model_name.startswith("llama3"):
        llm_instance = Llama3Llm(model_name, debug)
    elif model_name in ["phi3"]:
        llm_instance = Phi3ChatMLLlm(model_name, debug)
    elif model_name in ["mistral"]:
        llm_instance = MistralChatMLLlm(model_name, debug)
    else:
        raise ValueError(f"Unknown model name: {model_name}")

    print("llm_instance and LLM initialized")
    return llm_instance

