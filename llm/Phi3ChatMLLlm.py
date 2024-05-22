from llm.BaseOllamaLlm import BaseOllamaLlm

class Phi3ChatMLLlm(BaseOllamaLlm):
    def initialize_prompt(self):
        return ""

    def finalize_prompt(self):
        return "<|assistant|>"

    def get_role_prompt(self, role, prompt):
        return f"<|{role}|>{prompt}<|end|>"

    def get_stop_terms(self):
        return ["\n", "<|end|>"]

