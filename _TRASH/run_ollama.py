from langchain_community.llms import Ollama
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
import time

start_time = time.time()
llm_ollama = Ollama(model="llama3", callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),)
print(f"Time taken to create Ollama object: {time.time() - start_time} seconds")

start_time = time.time()
llm_ollama("Tell me a joke")
print(f"Time taken to invoke and print the result: {time.time() - start_time} seconds")

start_time = time.time()
llm_llamacpp = LlamaCpp(
    model_path="./models/Hermes-2-Pro-Mistral-7B.Q4_K_M.gguf",
    # model_path="./models/oh-2.5-m7b-q4k-medium.gguf",
    # n_gpu_layers=1,
    n_gpu_layers=30,
    n_ctx=3584, 
    n_batch=512,
    f16_kv=True,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
    verbose=True,
    # stop=["\n", "<|im_end|>"],
    stop=["<|im_end|>"],
)
print(f"Time taken to create LlamaCpp object: {time.time() - start_time} seconds")

start_time = time.time()
result = llm_llamacpp.invoke("Tell me a joke")
print(f"Time taken to invoke and print the result: {time.time() - start_time} seconds")
print(result)