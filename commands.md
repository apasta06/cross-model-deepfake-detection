# commands.md

## Python Setup

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

## Python Dependencies

- UI-focused dependencies: `python -m pip install -r requirements-ui.txt`
- Legacy full dependencies: `python -m pip install -r requirements.txt`

## Frontend Prerequisites

- Node.js 20+ recommended
- npm 10+ recommended
- Verified in this repo with `node -v` -> `v24.15.0`
- Verified in this repo with `npm -v` -> `11.12.1`

## Frontend Install

- Create app scaffold: `npm create vite@latest frontend -- --template react-ts --no-interactive`
- Install app dependencies: `cd frontend && npm install`
- Initialize Storybook: `cd frontend && npx storybook@latest init --yes`
- Install Playwright browser: `cd frontend && npx playwright install chromium`
- If Linux system packages are missing: `cd frontend && npx playwright install chromium --with-deps`

## Install Notes

- `requirements-ui.txt` is the lighter install for the Streamlit app.
- `requirements.txt` works, but it can take a long time because it downloads large packages.
- Storybook initialization also adds several frontend dev dependencies automatically.
- The repo no longer depends on a `.claude/` folder for frontend tooling.

## Run UI Commands

- Start the Streamlit app: `streamlit run streamlit_app.py`
- Start the React frontend: `cd frontend && npm run dev`
- Start Storybook: `cd frontend && npm run storybook`
- Build the React frontend: `cd frontend && npm run build`
- Build Storybook: `cd frontend && npm run build-storybook`
- Run Playwright smoke tests: `cd frontend && npm run test:e2e`

## Run Model Commands

- Show training CLI help: `python3 train_main.py --help`
- Show evaluation CLI help: `python3 eval_main.py --help`

## Frontend Review Helpers

- Capture a one-off Storybook screenshot: `cd frontend && npx playwright screenshot http://127.0.0.1:6006 frontend.png`
- Run Playwright in headed mode for debugging: `cd frontend && npx playwright test --headed`
- Open the Playwright HTML report: `cd frontend && npx playwright show-report`

## Verification

- Check Python in the active venv: `python --version`
- Check pip in the active venv: `python -m pip --version`
- For Streamlit, success means it starts and prints a local URL.
- For `train_main.py` and `eval_main.py`, `--help` is the safe verification command because full runs require local dataset and model paths.
- For the React frontend, success means `npm run build` completes without TypeScript or Vite errors.
- For Storybook, success means `npm run build-storybook` completes and creates `frontend/storybook-static/`.
- For Playwright, success means `npm run test:e2e` passes and can create artifacts under `frontend/artifacts/` when tests request them.
