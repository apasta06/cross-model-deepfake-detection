# Frontend Workflow

## Goal

Set up a React frontend workflow that lets OpenCode help with:

- UI design and architecture
- component and page implementation
- frontend stack decisions
- automated UI review without manually copying screenshots or DOM

The main constraint is that OpenCode cannot directly watch a live browser session in the same way a human can. The workflow below solves that by generating browser artifacts that can be inspected from the workspace.

## Recommended Setup

Use a separate `frontend/` app inside this repository.

- Python project stays at the repo root
- React app lives in `frontend/`
- Storybook lives inside `frontend/`
- Playwright lives inside `frontend/`

This keeps Python and Node dependencies isolated and avoids mixing UI tooling into the existing backend/research setup.

## Suggested Stack

- React
- TypeScript
- Vite
- Storybook
- Playwright

## Why Storybook

Storybook is useful for component-level UI development.

It gives us:

- isolated component rendering
- explicit UI states like loading, error, empty, success
- stable URLs for individual stories
- easier iteration on components without depending on full app flows

Examples of story states:

- `UploadCard/Empty`
- `UploadCard/Uploading`
- `ResultsPanel/Fake`
- `ResultsPanel/LowConfidence`
- `ReportDialog/Open`

## Why Playwright

Playwright is useful for browser automation and repeatable inspection.

It gives us:

- automated page opening
- clicking, typing, and navigation
- screenshot capture
- HTML/DOM snapshot capture
- console error detection
- responsive viewport checks
- repeatable test automation for later CI usage

In this workflow:

- Storybook defines what UI state should exist
- Playwright verifies what actually rendered

## Why Start With Playwright CLI First

Playwright CLI is a good first step before committing to test files.

Benefits:

- quick exploration
- easy local experimentation
- helps discover selectors, routes, and wait conditions
- helps us learn which states and artifacts matter

Once the workflow is understood, we can convert it into committed Playwright tests for reliable automation.

## Why Not Only Use Playwright CLI Long-Term

CLI is best for ad hoc exploration.

For long-term project use, Playwright test files are better because they are:

- repeatable
- version-controlled
- easier to maintain
- better for named scenarios and artifact generation

Use CLI first to learn the workflow, then formalize it into tests.

## Storybook vs Playwright

Storybook and Playwright solve different problems.

Storybook:

- component isolation
- state coverage
- easier UI iteration

Playwright:

- browser automation
- screenshots and DOM capture
- interaction testing
- responsive checks

Recommended approach: use both.

## Frontend Folder Layout

Suggested structure:

```text
.
├── frontend/
│   ├── src/
│   ├── .storybook/
│   ├── tests/
│   ├── artifacts/
│   ├── package.json
│   └── playwright.config.ts
├── streamlit_app.py
├── ui_mvp/
└── ...
```

Notes:

- `frontend/src/` contains React components and pages
- `frontend/.storybook/` contains Storybook config
- `frontend/tests/` contains Playwright tests
- `frontend/artifacts/` stores generated screenshots, HTML, and logs during review

## Installation Steps

Run these from the repository root unless stated otherwise.

### 1. Create the React app

```bash
npm create vite@latest frontend -- --template react-ts
```

### 2. Install frontend dependencies

```bash
cd frontend
npm install
```

### 3. Add Storybook

```bash
npx storybook@latest init
```

### 4. Add Playwright

If starting with CLI-style exploration:

```bash
npm install -D playwright
npx playwright install
```

If using the full Playwright project initializer instead, use that inside `frontend/` and adapt generated files as needed.

## Recommended Scripts

Add or keep scripts like these in `frontend/package.json`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build",
    "test:e2e": "playwright test"
  }
}
```

## Recommended Ignore Rules

Make sure `frontend/.gitignore` includes:

```gitignore
node_modules/
storybook-static/
playwright-report/
test-results/
artifacts/
```

## Suggested Workflow With OpenCode

### Design and implementation

Use OpenCode for:

- UI architecture discussion
- component structure
- page composition
- code generation
- design iteration

### Review workflow

The recommended loop is:

1. Build a React component or page.
2. Add Storybook stories for important states.
3. Run the frontend or Storybook locally.
4. Use Playwright to open the page or story.
5. Save screenshots, HTML, and other artifacts into the workspace.
6. Let OpenCode inspect those artifacts.
7. Refine the UI and repeat.

This removes the need to manually paste screenshots or DOM into chat.

## Two Review Modes

### 1. Storybook review

Best for:

- component states
- spacing and layout
- visual polish
- edge cases

### 2. Full app review

Best for:

- routing
- forms
- backend integration
- real user flows

Recommended usage:

- use Storybook for component development
- use the app itself for integration and end-to-end checks

## Artifact-Driven Review

Since OpenCode can read files in the workspace, the browser session should output artifacts such as:

- screenshots
- HTML snapshots
- accessibility snapshots
- console logs
- network or runtime errors

Example artifact paths:

- `frontend/artifacts/storybook/home.png`
- `frontend/artifacts/storybook/home.html`
- `frontend/artifacts/storybook/console.log`

This is the core workflow change that makes automated UI review practical.

## Suggested Progression

1. Create `frontend/` with Vite React TypeScript.
2. Install Storybook.
3. Install Playwright.
4. Use Playwright CLI first to explore the workflow.
5. Decide which stories/pages should be captured.
6. Convert the working process into committed Playwright tests.
7. Reuse those tests for repeatable UI review.

## Minimal First Milestone

The first milestone should be:

1. `frontend/` exists
2. Storybook runs
3. Playwright opens Storybook or the app
4. one screenshot is captured successfully
5. the artifact can be inspected from the repo

Once that works, the workflow is proven.

## Summary

Recommended approach for this repo:

- create a separate `frontend/` React app
- use Storybook for component-level UI development
- use Playwright for browser automation and artifact capture
- start with Playwright CLI to learn the flow
- later convert that flow into committed Playwright tests

This setup gives a practical collaboration loop where OpenCode can help design, generate, review, and refine UI with much less manual copy-pasting.
