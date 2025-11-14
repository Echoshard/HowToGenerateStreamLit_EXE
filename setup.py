# run_app.py
# --- Streamlit hidden/implicit imports ---
import streamlit.runtime.scriptrunner.magic_funcs   # Force cx_Freeze to bundle this
import streamlit.web.cli as stcli                   # Ensure Streamlit CLI is included

# --- OpenAI ---
import openai
import sys
import os
import base64
from pathlib import Path

# --- pyttsx3 (TTS / pysttx) ---
import pyttsx3
import pyttsx3.drivers.sapi5
import tempfile
import comtypes.stream

# --- Google Gemini ---
from google import genai
from google.genai import types

def main():
    sys.argv = ["streamlit", "run", "app.py", "--global.developmentMode=false"]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
