# Mesh & Load Studio

A separate macOS STEP-to-mesh preparation app with **Guided Setup and persistent integrated Codex chat**. Manual controls and agent tools operate on the same versioned project. Implemented 7 October 2026.

**Option 1:** import/inspect STEP, generate and locally refine Gmsh C3D10 tetrahedra or create structured C3D8 bricks for compatible six-face blocks, select/name CAD faces, define explicit elastic material, translational supports and force/pressure loads, independently check and export CalculiX INP. Save/reopen, immutable accepted mesh revisions, stale-write rejection, failure/cancellation recovery and optional bounded solver balance checks are included.

**Option 2 remains deferred:** result contours, convergence studies and solver-driven mesh adaptation. Abaqus export follows a separately validated adapter.

## Open the app

On this developer Mac, open `app/dist/mac-arm64/Mesh & Load Studio.app`, or run `npm start` from `app`. See [Setup and usage](docs/SETUP.md). Use the original built-in reference parts to explore the workflow. Codex uses the installed signed-in ChatGPT account; no application API key is required.

The local app uses external pinned Python/Gmsh and project-local CalculiX runtimes. It is not a portable, notarized distribution or proof of support for every STEP file. The supported first-release analysis model is one closed solid, homogeneous isotropic elasticity and linear static force/pressure loading. Unsupported topology is reported explicitly.

See [element families and brick scope](docs/ELEMENTS.md). Chat renders readable headings, lists, tables and code blocks; the icon/title sit at the left of the header.

## Evidence

- [Verification and current release boundary](docs/VERIFICATION.md)
- [Actual numerical benchmark data](docs/verification/kernel-results.json)
- [Local solver build and thread restriction](docs/verification/solver-runtime.md)
- [Real Codex refinement, manual override and solver evidence](docs/verification/agent-results.json)
- [Real Codex clarification evidence](docs/verification/agent-clarification.json)

## Planning history

- [Five options](OPTIONS.md)
- [Selected Option 1 plan](docs/plans/2026-10-07-option-1-delivery-plan.md)
- [Detailed architecture](docs/plans/2026-10-06-step-mesh-studio-design.md)
- [UI concepts](docs/UI_CONCEPTS.md)
- [Integrated agent workflow](docs/AGENT_WORKFLOW.md)
- [Reuse and accuracy discussion](docs/research/reuse-and-accuracy.md)

The source is GPL-2.0-or-later; see [LICENSE](LICENSE) and [dependency notices](app/NOTICE.md). No remote publishing has been performed.
