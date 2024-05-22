from llm.BaseOllamaLlm import BaseOllamaLlm

class Llama3Llm(BaseOllamaLlm):
    def initialize_prompt(self):
        return "<|begin_of_text|>"

    def finalize_prompt(self):
        return "<|start_header_id|>assistant<|end_header_id|>"

    def get_role_prompt(self, role, prompt):
        return f"<|start_header_id|>{role}<|end_header_id|>\n{prompt}<|eot_id|>"
    
    def get_stop_terms(self):
        return ["<|eot_id|>"]

