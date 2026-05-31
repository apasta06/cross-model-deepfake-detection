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
- FastAPI/multimodal inference path needs FastAPI, uvicorn, python-multipart, torch, torchvision, OpenCV, Pillow, facenet-pytorch, librosa, moviepy, and numpy available in the active environment.

## Install Notes
- `requirements-ui.txt` is the lighter install for the Streamlit app.
- `requirements.txt` works, but it can take a long time because it downloads large packages.

## Run FastAPI + React App
- Start backend from repo root: `source .venv/bin/activate && uvicorn api.main:app --reload --port 8000`
- Check liveness: `curl http://localhost:8000/api/v1/health`
- Check model catalog: `curl http://localhost:8000/api/v1/models`
- Start frontend from `frontend/`: `npm run dev`
- Open frontend: `http://127.0.0.1:5173`

## Multimodal Checkpoints
- Required visual checkpoint resolution order: `CHECKPOINT_MULTIMODAL_VIDEO`, `VIDEO_MODEL_PATH`, root `best_corrected_model.pt`.
- Optional audio checkpoint resolution order: `CHECKPOINT_MULTIMODAL_AUDIO`, `AUDIO_MODEL_PATH`, root `best_audio_model.pt`.
- Example explicit startup: `CHECKPOINT_MULTIMODAL_VIDEO=best_corrected_model.pt CHECKPOINT_MULTIMODAL_AUDIO=best_audio_model.pt uvicorn api.main:app --reload --port 8000`
- If audio checkpoint or audio track is missing, the API returns visual-only fallback with warnings.

## Run Frontend
- Start the Streamlit app: `streamlit run streamlit_app.py`
- Build React frontend from `frontend/`: `npm run build`
- Run React E2E tests from `frontend/`: `npm run test:e2e`

## Run Model Commands
- Show training CLI help: `python3 train_main.py --help`
- Show evaluation CLI help: `python3 eval_main.py --help`

## Verification
- Check Python in the active venv: `python --version`
- Check pip in the active venv: `python -m pip --version`
- Syntax-check multimodal API files: `python3 -m py_compile api/routes/analyze.py api/routes/meta.py api/deps.py api/models.py api/multimodal_detect.py tests/test_multimodal_detect.py`
- Run multimodal fusion tests: `python3 -m unittest tests/test_multimodal_detect.py`
- For Streamlit, success means it starts and prints a local URL.
- For `train_main.py` and `eval_main.py`, `--help` is the safe verification command because full runs require local dataset and model paths.
