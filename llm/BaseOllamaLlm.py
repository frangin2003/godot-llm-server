from llm.BaseLlm import BaseLlm
from langchain_community.llms import Ollama
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler

class BaseOllamaLlm(BaseLlm):
    def __init__(self, model_name, debug=False):
        super().__init__(model_name, debug)

    def create_llm(self):
        llm = Ollama(
            model=self.model_name,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
            verbose=True,
            # Model will stay loaded in memory
            keep_alive=-1,
            stop=self.get_stop_terms(),
        )
        # Preloads the model
        llm.invoke("")
    
        return llm

