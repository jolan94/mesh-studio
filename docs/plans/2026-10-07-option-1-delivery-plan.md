# Option 1 delivery plan

Decision date: 7 October 2026. User selected **Mesh & Load Studio first**, with **Solve & Refine Studio later**. Implementation began under the subsequent build request. The local Option 1 pilot and its verification evidence are recorded in [VERIFICATION](../VERIFICATION.md).

## Selected product

A separate Mac application for imported STEP geometry, chat-guided mesh settings, local refinement, materials, loads/supports and checked CalculiX INP export. Retain the reliable parts of Part Studio's installed Codex/project lifecycle and design a distinct geometry-first UI.

Selected UI: **Guided Setup + persistent integrated Codex chat**. The agent drives the same supported actions as the manual controls, across all preparation stages. The guide reflects operation results and lets users revisit settings; it does not require manual step-by-step completion. See [agent workflow](../AGENT_WORKFLOW.md).

Use existing numerical software: Gmsh/OCCT for geometry and meshing, CalculiX for verification runs. Our contribution is usable setup, region selection/mapping, typed AI orchestration, transparent checks and reproducible export. [Reuse/accuracy comparison](../research/reuse-and-accuracy.md) explains FreeCAD/SALOME alternatives.

## Release boundary

| First complete release | Later Option 2 / separate extensions |
|---|---|
| STEP inspection and unit handling; closed single-solid inputs | Assemblies/contact; shells/beam idealization; geometry editing |
| Quadratic tetrahedral structural export; global/local size controls | Broader element families and validated alternative mesh engines |
| Fixed and component displacement supports; pressure and distributed force | Bolt preload, couplings, nonlinear/dynamic/thermal setups |
| Explicit homogeneous linear-elastic material and linear-static deck | Result contours, deformed-shape inspection and result-based local adaptation |
| Mesh checks, setup checks, file checks and bounded optional solver check | User-run convergence studies and response-driven refinement |
| Save/reopen, revisions, cancellation, selected-revision export | Abaqus dialect adapter and licensed verification |

Benchmark solves are required during development. The first app may expose “Check with CalculiX” for supported complete cases. That is different from a full solve/results/convergence feature. Export status must record whether the user case was actually run; a missing solver cannot be reported as solver-passed.

## Architecture decisions

- Electron desktop host and isolated Python worker are the proposed first implementation, subject to the native runtime spike.
- Codex receives measured geometry and typed tool outcomes, then proposes settings/setup changes. Deterministic code executes the supported operations.
- One authoritative Gmsh/OCCT import supplies CAD region descriptors and mesh associations. The project schema is independent of backend-native IDs.
- Evaluate vtk.js and Three.js using an actual mesh/region-picking example before choosing the viewport. Do not assume the Part Studio viewer supports FEM selection/interior inspection.
- Separate modules for geometry inspection, mesh recipes, region mapping, analysis schema, deck export, independent checking and solver verification. Keep extension seams small; no plugin marketplace or simultaneous FreeCAD/SALOME adapters.
- Immutable source geometry and accepted revision files; checks associated with their exact hashes/settings.

## Delivery stages

### A. Prove geometry, mapping and export

Build a command-line spike before the application shell. Create original axial-bar, beam and pressure-block STEP fixtures from known reference dimensions. Import, generate quadratic tetrahedra, map selected CAD faces and write a supported complete deck. Independently reparse the exported file and run a real pinned CalculiX binary on Apple Silicon.

Acceptance: connectivity/order and pressure-face mapping pass; applied forces/moments and reactions agree within declared tolerances; displacement follows the appropriate analytic reference and mesh trend. Record unit conversions and actual native dependency versions. Failures are evidence, not automatic reasons to enlarge scope.

Inspect FreeCAD's existing Gmsh/CalculiX writer/workflow as a reference. When feasible, run the same original fixture in FreeCAD with explicit matched settings. This is a bounded comparison, not a second product. If exporter/region reuse would substantially simplify the spike, document the evidence and review that backend choice before the UI implementation.

### B. Prove local refinement and persistent regions

Add recipes for global size, selected-region local size and smooth distance transitions. Remesh a holed solid and a loaded beam. Rebuild the support/load sets, including quadratic boundary nodes; compare intended CAD-region identity, area and resultant load/moment.

Acceptance: two successful refinements preserve the setup, an ambiguous region requests clarification, and a failed candidate retains the previous checked mesh. Quality thresholds are tied to named metrics and benchmark results, never a generic percentage. Bound node/element count, time, memory and repair attempts.

### C. Build the geometry-first workspace

Implement import/units, scene navigation, face picking, named regions, CAD/mesh overlay, refinement controls, material/load/support inspector and visible checks. Save/reopen and export must work from the window before AI is connected.

Acceptance: a user can import a sample, select two end faces, define one material/load/support setup, refine, review and export an INP that matches the selected revision. Verify actual picker output and file export, not just screenshots. Build the selected [Guided Setup with Codex](../UI_CONCEPTS.md) layout; the persistent chat, step rail and settings share one project state.

### D. Connect AI assistance

Integrate the installed Codex bridge through a narrow typed action schema. Requests include the selected region, current unit/frame, accepted mesh/setup and diagnostics. Add clarification, real progress, Stop and bounded repairs.

Acceptance: one real signed-in agent request completes inspection → mesh → local refinement → explicit material/load/support setup → checks → export preparation. Verify the written INP and native save workflow. Also exercise ambiguity, a manual change followed by an agent edit, a real worker diagnostic, cancellation and agent usage/disconnection failure. Preserve accepted artifacts and maintain manual controls throughout.

### E. Verification and pilot delivery

Run the focused geometry/refinement/export benchmarks plus failure/recovery cases; test native import/save dialogs, Finder launch, process cleanup and revision integrity. Test a second Mac's documented prerequisites before claiming fresh-machine support. Record component licenses/notices and choose a compatible distribution model before bundling. Native runtime bundling/signing is a release gate, not assumed from a development build.

Completion: one fresh sample project can be reproduced from the saved geometry, mesh recipe and analysis setup; its displayed revision, exported file and verification report agree.

## Option 2 readiness

Store enough provenance now for later comparisons: geometry/setup hash, mesh recipe, counts, metrics, element family/order, solver version and selected verification measurements. Keep user-facing response/adaptation features deferred.

Later sequence: execute supported cases → parse/show results → define a quantity of interest → three-level mesh study → bounded local adaptation with a declared indicator. Every study must hold material, loads/support regions and geometry fixed, and report singularity concerns and budget termination honestly.

## Scope and schedule discipline

Stages A/B are the highest-risk work. Estimate delivery dates after those gates establish runtime packaging, quadratic mappings and refinement behavior. Complete one backend before adding another. The local pilot now implements this sequence. Portable runtime bundling, Developer ID signing/notarization, broader CAD coverage and a second-Mac test remain release gates; see the verification report for current evidence.
