# Integrated Codex operator

Decision recorded 7 October 2026: Guided Setup is the main workspace, with persistent Codex chat capable of completing every supported Option 1 operation. The local pilot now implements this contract through installed Codex app-server dynamic tools. Real end-to-end evidence is recorded in [VERIFICATION](VERIFICATION.md).

## Shared state and controls

The step rail, viewport, manual settings and Codex tools operate on one versioned project state. Each action declares its geometry/setup/mesh base revision. Reject stale writes, provide current diagnostics/context and let the agent replan. Selecting or manually changing a value immediately updates the next agent request's context.

Imported files are chosen through the app or explicitly supplied project paths. Codex can inspect the project's selected STEP and does not need the user to describe its geometry manually. Measurement and meshing come from the worker. Region references are resolved to measured CAD entities and mapped again after refinement.

## Capabilities in the first release

| Stage | Agent operations | Visible evidence |
|---|---|---|
| Geometry | Inspect imported STEP, report units/bodies/import issues, resolve/name selected regions | Measured report and highlighted CAD regions |
| Mesh | Choose supported algorithm/settings, generate quadratic tetra mesh, evaluate quality | Mesh preview, counts, named metrics and actual logs |
| Refinement | Apply global/local sizes and bounded repair from diagnostics | Candidate/accepted revisions, changed sizing region and checks |
| Material | Assign/edit explicit elastic properties and units | Editable material definition and section assignment |
| Loads/supports | Apply/edit/remove supported pressure, distributed force, fixed/component displacement constraints | Highlighted regions, vectors/symbols, values and regenerated sets |
| Review | Check mappings, units, references, load resultants and setup completeness; optionally run a bounded supported CalculiX check | Separate mesh/setup/file/solver statuses |
| Export | Write/check selected mesh or analysis INP, invoke native destination selection or a supplied project destination | Exact written artifact, revision/hash and report |
| Project | Save/reopen, inspect history, select an accepted revision and continue editing | Versioned state and preserved accepted artifacts |

Expose these as typed actions backed by the same deterministic code used by manual controls. The agent may chain operations from one request without asking approval at every stage. No arbitrary new dependency/code execution is needed to implement those supported actions.

## Conversation behavior

One request may complete a full supported preparation sequence. Persist the requirements brief, explicit assumptions, region selections and action results with the project so follow-up prompts retain context. Agent runtime sessions may be recreated; correctness must not depend on hidden chat memory.

Ask only when a critical input is missing, regions are ambiguous, or the request needs a new operation outside the supported contract. Do not invent material/load values or modify source geometry to get a mesh. Continue automatically after the clarification resolves the issue.

Stream actual stage changes and include Stop while work is active. Show compact outcomes linked to changed regions/settings/revisions. Preserve the accepted mesh on failed builds, cancellation and disconnection. The same mesh/setup can still be inspected and edited manually.

## Scope retained

“All operations” means the supported Option 1 preparation workflow, including export. Result visualization, convergence studies and solver-driven refinement remain Option 2. Unavailable or unrun checks remain explicitly identified; a successful agent turn is not artifact validation.

## Acceptance example

After a STEP is imported, send one request with mesh sizes, unique region selectors, elastic properties, support directions and a total force vector. The real agent must produce a checked complete INP using the tools, with the guide and editable controls reflecting the same accepted revision. Independently inspect and solve that exact file. Then change the force manually and ask the agent to refine: verify that the manual load value survives and that force/moment mapping is preserved.
