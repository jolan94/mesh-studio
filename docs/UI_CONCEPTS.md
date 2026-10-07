# UI directions for Mesh & Load Studio

Prepared 7 October 2026. User selected **Guided Setup with persistent integrated Codex chat**, with the agent able to drive the complete supported workflow. UI concepts remain illustrative, not solver or meshing evidence.

## Canvas Workbench — alternative

The model takes the center and most of the width. A slim left outline lists geometry and named regions; a contextual right inspector edits whatever is selected. A compact assistant dock runs across the bottom. Expand conversation history only when needed; selected regions become named context tokens in the prompt.

Top chrome: project, source geometry revision, units, accepted/pending mesh revision and Export. A task strip switches Geometry, Mesh, Setup and Review without forcing a wizard. The scene shows solid/mesh overlay, support symbols and load arrows. Avoid a permanent left chat column.

Click a face: highlight it and show its name/type/area; nearby actions offer Name region, Refine here, Add load or Add support. Clicking an existing load/support opens its definition and highlights its region. Numerical values can be changed without chat. The assistant can answer “what is selected?” from the same scene state.

A collapsible bottom tray contains checks and revision history. During work it shows real stage, elapsed time and Stop; the accepted model remains visible. Completion shows a compact change summary linked to the changed regions/settings. A failed load mapping highlights the affected region rather than leaving a generic red toast.

Why recommend it: imported geometry and inspection dominate this workflow; conversation supports the task without occupying half the app. It also accommodates future result overlays without restructuring the whole window.

## Guided Setup with Codex — selected

Left: a compact task path, Geometry → Mesh → Material → Loads/supports → Review/export. Center: a large CAD/mesh viewport and an editable contextual settings strip below it. Right: a persistent Codex conversation, including prompt input, selected-region references, operation progress, Stop and compact action results.

Codex is a full workflow operator. A single request can inspect the imported geometry, choose a supported meshing recipe, create/refine a mesh, name regions, assign explicit material/load/support values, check the setup and prepare INP export. The step rail updates from actual project/tool outcomes. It is a progress map and a way to revisit settings, not a sequence the user must manually complete.

The chat is available at every step, including after an export. Selected faces can be attached as named context tokens; requests referring to those tokens resolve against the current geometry revision. Manual edits and agent changes use the same application actions/schema and immediately update both settings and project context. A later agent action must not overwrite a manual change using stale state.

Example: “Mesh this part at 3 mm, refine the selected region to 1 mm, fix the minimum-X end and apply 100 N in negative Z to the other end. Use E=210000 MPa and nu=0.3. Prepare a CalculiX INP.” The agent handles the supported sequence, highlighting affected regions. It asks a focused question only for missing critical data or genuinely ambiguous selections, then continues from the resolved state.

Users can revisit a completed stage and skip analysis setup for mesh-only export. Show completion states and specific missing values. Do not force an approval on each step or hide the underlying parameters. A missing pressure direction offers an on-model choice instead of requiring a rewritten prompt.

The first-release scope remains Option 1. Solver-driven adaptation/result studies belong to Option 2. A bounded supported solver check can report whether a complete deck ran; it must not claim general solution convergence.

## Mesh Notebook

A project recipe records inspect, mesh, refine and setup operations as compact entries. Each entry names its inputs, changed settings, checked artifact and parent revision. Selecting an entry loads its mesh in an adjacent preview; entries expand to reveal checks and deck snippets.

Chat requests become reproducible operations rather than a long transcript. Compare the selected accepted mesh with a candidate through settings/metric deltas. Clearly distinguish a proposed operation, a failed run and an accepted artifact.

Best for reproducibility and engineering write-ups. Main risk: it gives less uninterrupted space to region picking. Recommended as a later History/Recipe view inside Canvas Workbench, rather than the default landing workspace.

## Shared interaction rules

- Working name: Mesh & Load Studio. No final branding decision yet.
- Use readable neutral surfaces, a restrained selection accent and a technical viewport. Color also has labels/symbols: fixed supports, forces, selected CAD region and failed elements remain distinguishable.
- Offer CAD, Mesh and Overlay display modes; preserve camera during settings edits when feasible. Fit/reset and clipping are discoverable.
- Explain element family/order and units in the inspector. “Fine” alone is insufficient; expose target sizes and transitions.
- Keep Geometry accepted, Mesh checked, Setup complete and Solver run status distinct. Never show a green analysis-success status from mesh generation alone.
- Support mouse and keyboard selection, list-based region selection, focus indication, reduced motion and usable resizing. Hide secondary panels before shrinking scene labels below readable size.
- Export offers Mesh INP or Analysis INP with visible revision/validation status. Incomplete analysis can still export a mesh; unavailable checks are identified.
- Avoid decorative metric dashboards, guessed accuracy scores, raw agent/tool protocol text and a stress-result screen before Option 2 exists.

## Selected combination

Guided Setup as the main interface, persistent Codex chat as a full operator, and Mesh Notebook concepts as a collapsible recipe/history tray. Preserve a large central viewport; move detailed forms to the selected-step inspector rather than replacing the conversation.
