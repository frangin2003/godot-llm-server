from llm.BaseLlm import BaseLlm
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from dotenv import load_dotenv
import os


class OpenAILlm(BaseLlm):

    def initialize_prompt(self):
        return []

    def finalize_prompt(self):
        return []

    def get_role_prompt(self, role, prompt):
        if prompt is None:
            return []
        if role == "user":
            return [HumanMessage(content=[{"type": "text", "text": prompt}])]
        elif role == "system":
            return [SystemMessage(content=[{"type": "text", "text": prompt}])]
        else:
            return [AIMessage(content=[{"type": "text", "text": prompt}])]
        
    def init_llm(self):
        return ChatOpenAI(
            model=self.model_name,
            api_key=os.getenv("API_KEY"),
            temperature=0.0,
            model_kwargs={"top_p":0.1},
            max_tokens=1000,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()],
        )

