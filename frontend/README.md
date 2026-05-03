# Frontend

This folder contains the React frontend that will eventually replace the current Streamlit UI.

## Stack

- React
- TypeScript
- Vite
- Storybook
- Playwright

## Prerequisites

- Node.js 20+ required by current Vite and Playwright docs
- npm 10+

Tested in this repo with:

- Node.js `v24.15.0`
- npm `11.12.1`

## Install

Run from the repository root unless noted otherwise.

```bash
npm create vite@latest frontend -- --template react-ts --no-interactive
cd frontend
npm install
npx storybook@latest init --yes
npx playwright install chromium
```

If Playwright reports missing Linux packages, run:

```bash
cd frontend
npx playwright install chromium --with-deps
```

## Scripts

Run these from `frontend/`.

```bash
npm run dev
npm run build
npm run storybook
npm run build-storybook
npm run test:e2e
```

## What Each Command Does

- `npm run dev`: starts the Vite app on the default dev port
- `npm run build`: type-checks and builds the frontend
- `npm run storybook`: starts Storybook on port `6006`
- `npm run build-storybook`: builds the static Storybook site
- `npm run test:e2e`: runs the committed Playwright smoke test in `tests/`

## Verified Outputs

The current repo setup has already been verified with:

- a successful Vite production build
- a successful Storybook static build
- a passing Playwright smoke test against the app
- artifact capture under `frontend/artifacts/`

Example generated artifacts:

- `frontend/artifacts/app/home.png`
- `frontend/artifacts/app/home.html`
- `frontend/artifacts/storybook/home.png`

## Files You Should Commit

- source files in `src/`
- Storybook config in `.storybook/`
- Playwright tests in `tests/`
- Playwright config in `playwright.config.ts`
- `package.json` and lockfile updates

## Files You Should Not Commit

These are ignored at the repository root:

- `frontend/node_modules/`
- `frontend/dist/`
- `frontend/dist-ssr/`
- `frontend/storybook-static/`
- `frontend/playwright-report/`
- `frontend/test-results/`
- `frontend/artifacts/`

## Playwright CLI vs Playwright Tests

Use both, for different purposes.

- Playwright CLI is good for quick ad hoc browser checks and screenshots
- `@playwright/test` is better for committed, repeatable checks in the repo

This repo currently uses both:

- `playwright` for CLI-style browser automation
- `@playwright/test` for committed tests and the `npm run test:e2e` workflow

## Note About `.claude` Skills

This repo no longer relies on a `.claude/` folder for frontend automation.

If a teammate previously used a local Playwright CLI skill from `.claude/`, that is now replaced by the repo-local Node tooling above. Frontend development and browser verification should work with standard npm scripts and Playwright commands.
