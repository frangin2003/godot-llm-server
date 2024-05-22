from llm.BaseOllamaLlm import BaseOllamaLlm

class MistralChatMLLlm(BaseOllamaLlm):
    def initialize_prompt(self):
        return ""

    def finalize_prompt(self):
        return "<|im_start|>assistant\n"

    def get_role_prompt(self, role, prompt):
        return f"<|im_start|>{role}\n{prompt}\n<|im_end|>"

    def get_stop_terms(self):
        return ["\n", "<|im_end|>"]

