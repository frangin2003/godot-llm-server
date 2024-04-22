# llm-server

# llm-server-cuda
## Prerequisites
- Anaconda https://www.anaconda.com/download
- CUDA (you need a NVidia Developer account)

### Install CUDA
https://developer.nvidia.com/cuda-downloads (< 3GB)
Installation Instructions:
Double click cuda_12.4.1_551.78_windows.exe
Follow on-screen prompts
Additional installation options are detailed here:
https://docs.nvidia.com/cuda/cuda-installation-guide-linux/#meta-packages

##  Create a python env with Anaconda
```bash
conda create --name llm-server-cuda
conda activate llm-server-cuda
```

## Install llama-cpp-python with CUDA enabled
```bash
set CMAKE_ARGS=-DLLAMA_CUBLAS=on
set FORCE_CMAKE=1
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir
```

# TTS
https://huggingface.co/models?pipeline_tag=text-to-speech&sort=downloads
## Suno AI
### Install PyTorch with CUDA
https://pytorch.org/get-started/locally/
```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

conda create -n coquitts python=3.10
conda activate coquitts
conda install pytorch torchvision torchaudio pytorch-cuda=11.7 -c pytorch -c nvidia
conda install --file requirements.txt
cd (directory of tts)
pip install -r requirements.txt
python setup.py develop
#use python script to produce tts results

# Coqui model speakers
```bash
tts --model_name tts_models/multilingual/multi-dataset/xtts_v2 --list_speaker_idxs
```
# Conda
Sure, here's a cheat sheet for some common Conda commands:

1. **Create a new environment**: 
   ```bash
   conda create --name myenv
   ```

2. **Create a new environment with specific Python version**:
   ```bash
   conda create --name myenv python=3.6
   ```

3. **Activate an environment**:
   - On Windows:
     ```bash
     activate myenv
     ```
   - On macOS and Linux:
     ```bash
     source activate myenv
     ```

4. **Deactivate an environment**:
   - On Windows:
     ```bash
     deactivate
     ```
   - On macOS and Linux:
     ```bash
     source deactivate
     ```

5. **List all environments**:
   ```bash
   conda env list
   ```

6. **Install a package in the active environment**:
   ```bash
   conda install numpy
   ```

7. **Install a specific version of a package**:
   ```bash
   conda install numpy=1.10
   ```

8. **Update a package**:
   ```bash
   conda update numpy
   ```

9. **Update Conda itself**:
   ```bash
   conda update conda
   ```

10. **Remove a package**:
    ```bash
    conda remove numpy
    ```

11. **Remove an environment**:
    ```bash
    conda env remove --name myenv
    ```

12. **Export an environment to a file**:
    ```bash
    conda env export > environment.yml
    ```

13. **Create an environment from a file**:
    ```bash
    conda env create -f environment.yml
    ```

Remember to replace `myenv` with the name of your environment and `numpy` with the name of the package you want to install or remove.