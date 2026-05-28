`# AGENTS.md

## ⛔ Mandatory Rules (Read First, Apply Always)

These rules apply at every context start, mid-session, and after any restart.
Violating any of them is a hard error - not a judgment call.

1. **NEVER make any code change without explicit user approval first.**
   - Present the proposed change (file, location, what and why) and wait for the user to say "go ahead", "yes", "do it", or equivalent.
   - "Continue" or "proceed" on a previously approved plan is sufficient only if the exact change was described and approved in that same session before the context restart.
   - When in doubt: ask, do not act.

2. **NEVER commit or push without explicit user instruction.**

3. **After a context restart, always summarize what you know from AGENTS.md and ask the user how to proceed - do not resume coding autonomously.**

4. **If a command, path, class name, endpoint, or workflow is uncertain, say so explicitly.**
   - Do not invent commands or repository structure.

---

## Repository Context

### Known Facts
- **Language**: Python 3.x (repo includes `requirements.txt` and `requirements-ui.txt`)
- **UI Framework**: Streamlit
- **ML Stack**: PyTorch-based deepfake model integration in MVP analysis pipeline
- **Repository Type**: Research + application code for cross-model deepfake detection
- **Main app entry point**: `streamlit_app.py`
- **Legacy CLI entry points**: `train_main.py`, `eval_main.py`

### Project Structure
```
cross-model-deepfake-detection/
├── streamlit_app.py
├── train_main.py
├── eval_main.py
├── ui_mvp/
│   ├── analysis.py
│   ├── config.py
│   ├── reporting.py
│   ├── schemas.py
│   └── storage.py
├── frontend/
├── tests/
├── Unimodal/
├── Multimodal/
├── Ensemble/
└── utils/
```

### Package / Module Areas
**Confirmed top-level areas:**
- `ui_mvp/` - Streamlit MVP analysis, reporting, storage, and schemas
- `tests/` - tests for MVP and supporting behavior
- `Unimodal/` - unimodal training and evaluation code
- `Multimodal/` - multimodal code
- `Ensemble/` - ensemble evaluation code
- `utils/` - shared utilities
- `frontend/` - standalone React frontend work

---

## Verified Commands

**To verify commands safely:**
1. Ask user to test the command when local environment access is needed
2. Add successful commands to this section
3. Do not claim a command is correct unless it was verified from this repo or by successful execution

| Command | Description | Notes |
|---------|-------------|-------|
| `pip install -r requirements.txt` | Install legacy/full Python dependencies | Documented in repo; not executed in this session |
| `pip install -r requirements-ui.txt` | Install Streamlit-focused Python dependencies | Documented in repo; not executed in this session |
| `streamlit run streamlit_app.py` | Run Streamlit MVP app | Documented in repo; not executed in this session |
| `source .venv/bin/activate && uvicorn api.main:app --reload --port 8000` | Run FastAPI backend | Executed successfully by user; backend serves `/api/v1` endpoints |
| `curl http://localhost:8000/api/v1/health` | Check FastAPI liveness | Executed successfully by user; returned `{"status":"ok"}` |
| `curl http://localhost:8000/api/v1/models` | List API model options | Executed successfully during this session |
| `VITE_API_BASE=http://127.0.0.1:8000/api/v1 npm run dev` | Run React frontend connected to local API | User verified this fixes local CORS/localhost issue |
| `npm run build` | Build standalone frontend | Executed successfully in `frontend/` during this session |
| `npm run build-storybook` | Build Storybook static site | Executed successfully in `frontend/` during this session |
| `npm run test:e2e` | Run Playwright E2E tests | Executed successfully in `frontend/` during this session |

### Local API + Frontend Workflow

For the current FastAPI + React integration, use two terminals:

1. Backend from repository root:
```bash
source .venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

2. Frontend from `frontend/`:
```bash
npm run dev
```

`frontend/package.json` sets `VITE_API_BASE=http://127.0.0.1:8000/api/v1` for `npm run dev`. Open the frontend at `http://127.0.0.1:5173` to avoid WSL/browser `localhost` resolution issues.

The frontend loads models from `GET /api/v1/models`, defaults to `EFFICIENTB0`, uploads media to `POST /api/v1/analyze`, and displays the returned `AnalysisResult`.

`EFFICIENTB0` uses the default root checkpoint `best_corrected_model.pt` when present. Other models need checkpoint environment variables before backend startup, for example:
```bash
CHECKPOINT_MESO4=Unimodal/weights/video/Meso4_realA_fakeC.pt uvicorn api.main:app --reload --port 8000
```

---

## Working Style

This repository follows a human-in-the-loop development workflow:
1. **Plan** the change and get approval
2. **Implement** after explicit approval
3. **Validate** via commands, tests, or user-reported run results
4. **Debug** using exact user-provided errors/logs

### Development Approach
- **Prefer small, focused changes** over large refactors
- **Follow existing patterns** in nearby files before creating new ones
- **Use exact evidence** from logs, errors, and test results
- **Inspect adjacent files** in the same module to match local conventions
- **Do not claim verification** unless something was actually tested
- **Do not say a fix is confirmed** unless validated by successful command/test/user report

### When Debugging
- Identify the **first meaningful exception** and root cause chain
- Separate **startup failures** from **runtime failures**
- Use **specific error messages** instead of generic guesses
- Ask for the most relevant missing output only when needed

---

## Boundaries & Constraints

### What NOT to assume
- Exact dataset availability or local file paths
- GPU availability or CUDA setup
- Model checkpoint compatibility without evidence
- Endpoint URLs/ports unless shown in code or run output
- Performance claims without benchmark evidence

### Before making changes
1. **Describe the change** (files, purpose, expected effect)
2. **Wait for approval** before editing
3. **Follow local patterns** from the same module/package
4. **Ask about uncertainties** rather than guessing

### ML / Analysis Pipeline Caution
Before modifying model inference, sampling, or risk logic:
- Review current behavior in `ui_mvp/analysis.py` and `ui_mvp/config.py`
- Keep threshold logic and reporting semantics consistent unless user requests a behavior change
- Call out any effect on verdict/confidence/risk interpretation

---

## Response Format

When helping with this repository:
1. **State diagnosis** briefly
2. **Propose minimal change** needed
3. **List specific files** to edit
4. **Provide validation steps** if known
5. **Mention what remains unverified**
6. **Separate confirmed facts from assumptions**
7. **Wait for approval** before implementing
