# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[],  # No .env file included
    hiddenimports=[
        # Core LangChain dependencies
        'langchain_community',
        'langchain_core',
        'langchain_openai',
        
        # Audio processing
        'PyAudio',  # Required by SpeechRecognition
        'pydub',
        'soundfile',
        'speech_recognition',
        
        # Windows-specific
        'pythoncom',
        'win32com',
        'win32com.client',
        
        # Web communication
        'websockets',
        
        # Environment and config
        'dotenv',
        
        # Image processing
        'PIL',
        'PIL._imaging'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['torchvision', 'torchaudio', 'pip-review'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='run',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
