from llm.OpenAILlm import OpenAILlm
from llm.Llama3Llm import Llama3Llm
from llm.Phi3ChatMLLlm import Phi3ChatMLLlm
from llm.MistralChatMLLlm import MistralChatMLLlm

def create_llm_instance(model_name, debug=False):
    llm_intance = None
    if model_name in ["gpt4", "gpt4-turbo", "gpt4o"]:
        llm_intance = OpenAILlm(model_name, debug)
    elif model_name in ["llama3"]:
        llm_intance = Llama3Llm(model_name, debug)
    elif model_name in ["phi3"]:
        llm_intance = Phi3ChatMLLlm(model_name, debug)
    elif model_name in ["mistral"]:
        llm_intance = MistralChatMLLlm(model_name, debug)
    else:
        raise ValueError(f"Unknown model name: {model_name}")

    print("llm_intance and LLM initialized")
    return llm_intance

