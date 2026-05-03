# AGENTS.md

## Project
- Python repository for deepfake detection and dataset-related research code.
- Main app entry point: `streamlit_app.py`
- Legacy CLI entry points: `train_main.py`, `eval_main.py`
- React frontend lives in `frontend/` and is intended to replace the Streamlit UI over time.

## Structure
- `frontend/` - React/Vite frontend with Storybook and Playwright tooling
- `ui_mvp/` - Streamlit MVP analysis, reporting, storage, and schemas
- `tests/` - tests for the MVP layer
- `Unimodal/` - unimodal training and evaluation code
- `Multimodal/` - multimodal code
- `Ensemble/` - ensemble evaluation code
- `utils/` - shared training/evaluation utilities
- `images/` - README assets

## Commands We Know
- Install legacy dependencies: `pip install -r requirements.txt`
- Install UI-focused dependencies: `pip install -r requirements-ui.txt`
- Run the Streamlit app: `streamlit run streamlit_app.py`
- Install frontend dependencies: `cd frontend && npm install`
- Run the frontend app: `cd frontend && npm run dev`
- Run Storybook: `cd frontend && npm run storybook`
- Run Playwright smoke tests: `cd frontend && npm run test:e2e`

## Notes
- Prefer working in the current repo structure rather than introducing new top-level layouts.
- Check the existing module before adding new files.
- Keep changes focused and minimal.
- Frontend generated outputs are ignored at the repo root instead of via a nested `frontend/.gitignore`.
