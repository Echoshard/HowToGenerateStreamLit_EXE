# How to Generate a Streamlit EXE Build (Using cx_Freeze)

Based on: https://youtu.be/tmc67kpzq88

This guide explains how to convert a **Streamlit app** into a standalone
**Windows EXE** using `cx_Freeze`.\

It also includes notes for OpenAI, Google Gemini, and pyttsx3 (TTS)
support.

------------------------------------------------------------------------

## 📦 Overview

To build a standalone executable:

1.  Update your `app.py` and `setup.py`
2.  Add hidden/implicit imports (Streamlit, OpenAI, Gemini, pyttsx3)
3.  Run `cxFreeze.bat`
4.  Copy `app.py` and `setup.py` into the new `ToRun` folder
5.  Run your EXE
6.  (Optional) Change the EXE icon

------------------------------------------------------------------------

## 🚀 1. Add Required Imports (Hidden Dependencies)

Some libraries used by Streamlit, OpenAI, Gemini, and pyttsx3 are **not
automatically detected** by cx_Freeze.

Add these imports inside your **`setup.py`** to force cx_Freeze to
include them:

``` python
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
```

If you are using new python lobaries this may be a bit of trial and error when the `EXE` fails just add them one by one until they work!

------------------------------------------------------------------------

## ⚙️ 2. Run cx_Freeze

After your `setup.py` is ready, run:

    cxFreeze.bat

This process may take some time depending on your dependencies.

------------------------------------------------------------------------

## 📁 3. Prepare the Output Folder

After the build completes, you should see a folder named:

    ToRun/

Inside this folder:

1.  Copy your `app.py`
2.  Copy your `setup.py`
3.  Run the generated `.exe` inside the folder

Streamlit often requires original Python files to remain accessible.

------------------------------------------------------------------------

## 🎨 4. Optional: Change the EXE Icon

You can update the generated EXE's icon using:

-   **WIN_ChangeIconForEXE**

Replace the default cx_Freeze icon with a png!

------------------------------------------------------------------------

## 📝 Notes

-   If your EXE crashes or fails to run, you likely need to **add more
    hidden imports** to `setup.py`.
-   Ensure any API keys (OpenAI, Gemini) are accessible in environment
    variables or config files.
-   pyttsx3 (`sapi5`) and Streamlit can introduce extra
    dependencies---test thoroughly.
-   Virus scanners don't like this so they may attempt to quarantine it 🦠

------------------------------------------------------------------------
