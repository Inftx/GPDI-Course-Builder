# Copilot Instructions for GPDI Course Builder

## Project context
- This project is a Streamlit-based AI lecturer assistant.
- Keep the application architecture intact:
  - Streamlit UI logic belongs in the app entrypoint and page modules under pages/.
  - Business logic belongs in services/ and modules/.
  - Project data and generated outputs belong under projects/ and outputs/.

## Core engineering rules
- Reuse existing services and modules instead of introducing parallel implementations.
- Never duplicate code when an existing helper, service, or module can be reused.
- Keep business logic inside services/ and modules/.
- Keep Streamlit pages focused on UI, state handling, and user interaction.
- Preserve the existing project architecture when adding features or refactoring code.
- Use pathlib for file handling rather than manual string-based path manipulation.
- Use type hints where appropriate to improve clarity and maintainability.
- Keep functions small, focused, and easy to test.
- Verify imports and dependencies before finalizing changes.

## Implementation expectations
- Prefer small, targeted changes over broad rewrites.
- Follow the existing structure and naming patterns in the repository.
- When modifying functionality, update the relevant service or module rather than placing logic directly in page code.
- If a new feature requires persistence, generation, or processing, add or extend the appropriate service layer instead of embedding logic in the UI.

## Verification checklist after every change
- Verify syntax for the affected Python files.
- Verify imports and dependency resolution.
- Verify existing functionality with the most relevant local check, such as running the affected page, script, or test.
- If the change affects a workflow, confirm that the workflow still behaves correctly end to end.

## Response expectations
- Return only the files that were modified.
- Prefer concise, implementation-focused updates.
- Do not introduce architectural drift or bypass existing services.
