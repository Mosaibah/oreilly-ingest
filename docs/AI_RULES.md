# AI Governance & Rules

## Non-Negotiable Working Rules

Rule 1: No coding before shaping.
Rule 2: No implementation before plan review.
Rule 3: One task, one branch, one slice.
Rule 4: No agent changes architecture without approval.
Rule 5: Two failed fixes = stop and diagnose.
Rule 6: Done means tested, reviewed, documented, and deployable.
Rule 7: Fixed time, variable scope.

These rules override convenience, speed, and agent suggestions. If any task conflicts with these rules, stop and report the conflict before proceeding.

## Core Mandates
1. **Shaping First:** No coding before shaping documentation is approved.
2. **Review First:** No implementation before a strategic plan is reviewed.
3. **Isolation:** One task, one branch, one slice.
4. **Stability:** Two failed fixes = stop and diagnose.

## Implementation Agent (Gemini)
Gemini is an **implementation agent**, not the product owner. It operates under strict boundaries defined in the `/docs` folder.

### Required Implementation Prompt Format
When starting an implementation task, the user should provide:
- **Role:** (e.g., Senior Python Engineer)
- **Goal:** Clear objective.
- **Context:** Relevant docs/files.
- **Scope:** Files allowed to change.
- **Constraints:** Patterns to follow/avoid.
- **Required Changes:** Specific logic updates.
- **Do Not Do:** Hard boundaries.
- **Verification:** How to test.
- **Output Report:** Format for completion.

## Allowed Behavior
- Surgical edits to existing files within scope.
- Creating new test files to verify changes.
- Reading any file in the project to understand context.
- Proposing architectural improvements (via `Inquiry`).

## Forbidden Behavior
- **Broad Refactors:** Do not "clean up" unrelated code.
- **New Dependencies:** Do not add entries to `requirements.txt` without approval.
- **Silent Failures:** Do not suppress errors or types.
- **Architecture Shifts:** Do not move logic between layers (e.g., core to plugin) without approval.

## Stop Rules
- If a test fails twice after attempted fixes, **STOP**. Summarize the failure, list assumptions, and ask for guidance.
- If the requested change contradicts `ARCHITECTURE.md` or `AI_RULES.md`, **STOP** and clarify.

## Required Output Report
Every agent run must conclude with:
1. **Summary of changes.**
2. **List of modified files.**
3. **Test results/Verification output.**
4. **Any new assumptions or risks identified.**
5. **Recommended next step.**
