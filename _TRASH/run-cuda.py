from llama_cpp import Llama
llm = Llama(model_path="./models/Hermes-2-Pro-Mistral-7B.Q4_K_M.gguf", 
            n_gpu_layers=30, n_ctx=3584, n_batch=521, verbose=True)
# adjust n_gpu_layers as per your GPU and model
output = llm("Q: Name the planets in the solar system? A: ", max_tokens=32, stop=["Q:", "\n"], echo=True)
print(output)