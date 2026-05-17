# frontendAgent.md

## Purpose

Use this guide when an OpenCode agent is assigned frontend work in this repository.
The frontend lives in `frontend/` and is currently a standalone React + TypeScript app with Tailwind, Storybook, and Playwright.

## Scope

Frontend agent tasks typically include:

- Building or refining React UI components in `frontend/src/`
- Preserving ML-evidence semantics in the UI (frames, probabilities, risk labels)
- Updating Storybook stories for new/changed components
- Updating Playwright tests for user-visible behavior
- Running frontend verification commands before reporting completion

Do not modify backend Python/Streamlit files unless explicitly requested.

## Required Working Rules

1. Keep changes small and focused.
2. Match existing code style and patterns in nearby frontend files.
3. Do not claim something works without running verification commands.
4. If behavior/requirements are ambiguous, state assumptions explicitly.
5. Prefer accessible selectors and semantic markup to improve test reliability.

## Frontend Architecture Snapshot

- Entry: `frontend/src/main.tsx`
- Main page composition: `frontend/src/App.tsx`
- Shared types: `frontend/src/types/analysis.ts`
- Mock fixture: `frontend/src/mocks/analysisResult.ts`
- Shared helpers: `frontend/src/lib/`
- UI components: `frontend/src/components/`
- Storybook stories: `frontend/src/**/*.stories.tsx`
- Playwright tests: `frontend/tests/`

## ML-Evidence UX Constraints (Important)

When building UI features, preserve these core product goals:

- Clearly show which sampled frames are suspicious.
- Show per-frame fake probability in a readable format.
- Preserve risk semantics (`likely_real`, `uncertain`, `likely_fake`).
- Keep flagged-frame signaling visible and consistent.
- Keep timeline/thumbnail/table/frame-detail selection synchronized.

If you change any of the above behavior, call it out explicitly in your summary.

## Standard Workflow for Frontend Changes

1. Inspect current component/test/story files before editing.
2. Implement minimal code changes.
3. Update or add Storybook stories if UI behavior changes.
4. Update or add Playwright tests for user-facing interactions.
5. Run verification commands.
6. Report:
   - what changed,
   - what was tested,
   - what remains unverified.

## Verification Commands (run in `frontend/`)

- Install dependencies: `npm install`
- Build app: `npm run build`
- Build Storybook: `npm run build-storybook`
- Run E2E tests: `npm run test:e2e`

If tests fail, include exact failing test names and root-cause notes.

## Playwright Guidance

- Prefer scoped locators (e.g., by labeled region/component) to avoid collisions.
- Use `data-testid` only when semantic/accessible selectors are insufficient.
- Cover both desktop and mobile behavior (config already includes both projects).
- Keep assertions focused on visible user outcomes, not implementation details.

## Storybook Guidance

When creating or updating stories:

- Include realistic states for likely fake, uncertain, and likely real where relevant.
- Keep stories deterministic (avoid random values/time-based variance).
- Use mock fixture data from `frontend/src/mocks/analysisResult.ts` when possible.

## File/Commit Hygiene

- Do not commit generated artifacts (`dist/`, `storybook-static/`, `playwright-report/`, `test-results/`).
- Keep lockfile updates (`package-lock.json`) only when dependency changes are intentional.
- If an unrelated file is dirty, do not revert it unless explicitly requested.

## Done Criteria (Frontend Task)

A frontend task is done when:

1. UI behavior requested by the user is implemented.
2. Related Storybook and Playwright coverage is updated as needed.
3. `npm run build`, `npm run build-storybook`, and `npm run test:e2e` pass, or failures are documented clearly.
4. Final report separates confirmed facts from assumptions/unverified items.
