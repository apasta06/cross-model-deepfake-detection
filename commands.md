# commands.md

## Venv Setup

### WSL / macOS
- Create venv: `python3 -m venv .venv`
- Activate venv: `source .venv/bin/activate`
- Verify interpreter: `which python`

### Windows
- Create venv: `py -m venv .venv`
- PowerShell activate: `.venv\Scripts\Activate.ps1`
- Command Prompt activate: `.venv\Scripts\activate.bat`
- Git Bash activate: `source .venv/Scripts/activate`
- Verify interpreter: `where python`

## Install Dependencies
- UI-focused dependencies: `python -m pip install -r requirements-ui.txt`
- Legacy full dependencies: `python -m pip install -r requirements.txt`

## Install Notes
- `requirements-ui.txt` is the lighter install for the Streamlit app.
- `requirements.txt` works, but it can take a long time because it downloads large packages.

## Run Frontend
- Start the Streamlit app: `streamlit run streamlit_app.py`

## Run Model Commands
- Show training CLI help: `python3 train_main.py --help`
- Show evaluation CLI help: `python3 eval_main.py --help`

## Verification
- Check Python in the active venv: `python --version`
- Check pip in the active venv: `python -m pip --version`
- For Streamlit, success means it starts and prints a local URL.
- For `train_main.py` and `eval_main.py`, `--help` is the safe verification command because full runs require local dataset and model paths.
