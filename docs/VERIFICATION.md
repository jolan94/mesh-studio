# Local pilot verification — 7 October 2026

The implemented Option 1 app was tested on this Apple Silicon Mac. Guided Setup and the integrated signed-in Codex operate on one autosaved, versioned project. This is a verified local pilot, not a portable or notarized release.

## Executed checks

| Area | Evidence and result |
| --- | --- |
| Host/worker integration | Three real-worker integration tests passed: revisions and stale-write rejection; setup/export validation and save/reopen integrity; actual worker cancellation preserving the accepted mesh. [Log](verification-host.log). |
| Geometry and numerical validation | Eight Python tests passed. Thirteen actual CalculiX solves cover axial loading/refinement, cantilever bending, HXT, six pressure face orientations, and curved-bore pressure intersecting a restrained boundary. Open surfaces/multiple solids are inspection-only; STEP source units are normalized. [Log](verification-kernel.log), [data](verification/kernel-results.json). |
| Independent INP validation | Parser checks node/element references, C3D10 corner orientation and shared midside nodes, exterior surface faces, finite values and sufficient rigid-body restraint. Export/solver evidence is bound to the exact deck SHA-256. |
| Real Codex workflow | Installed ChatGPT-signed-in Codex prepared and exported an axial bar; a follow-up preserved a manual 750 N override while refining and running CalculiX. Unsupported nonlinear contact/adaptation left the project unchanged. [Evidence](verification/agent-results.json). |
| Missing/ambiguous input | Real Codex asked for material/load details and disambiguation between two faces named Mount, without inventing physics or exporting an analysis. [Evidence](verification/agent-clarification.json). |
| Interruption/disconnection | Real agent cancellation and child-process termination preserved the accepted project and reported the interruption. [Evidence](verification/agent-lifecycle.json). |
| Native manual workflow | Developer app: reference cantilever, manual 4 mm mesh, E=210000 MPa/nu=0.3, fixed end and -100 N Z force, measured-face selection, independent analysis check and native INP save. The exact saved deck also executed successfully in CalculiX. |
| Packaged end-to-end workflow | Actual `.app`: native STEP picker imported the original axial bar; native project dialog created `pilot-projects/native-axial-bar.meshstudio`; integrated Codex generated 933 C3D10 elements/1717 nodes with 4 mm global and 2 mm xmax refinement, explicit material, xmin restraint and +750 N X load. Analysis and solver balance passed; chat exported `native-prepared.inp`; native save exported `pilot-projects/native-verified-axial-bar.inp`. The saved file independently passes and its hash matches the solver deck. [Evidence](verification/native-package.json). |
| Package integrity | `node app/scripts/check-package.cjs` confirms packaged source matches tested source, Three viewer dependencies, local camera controls, STEP fixtures and runtime configuration. `codesign --verify --deep --strict` passes for the local ad-hoc signature. The final package reopens the saved prepared project and conversation. |

The axial benchmark differs from FL/EA by approximately 0.8%, consistent with its fully fixed Poisson-constrained end. The cantilever mean tip deflection differs from Euler–Bernoulli by approximately 0.0285% for this benchmark. These examples are evidence for the implemented paths, not an accuracy guarantee for arbitrary geometry. The application reports that convergence is unestablished.

## Corrections made during verification

- Matched the quadratic tetrahedron ordering to CalculiX, including the final two midside nodes; mapped boundary triangles to actual parent element faces.
- Used quadratic surface integration for distributed force and pressure, including curved surfaces and force/moment accounting.
- Subtracted loads on restrained degrees of freedom when interpreting CalculiX RF. RF contains the net external force at a node; it is not automatically a pure support reaction.
- Limited exported numeric fields to CalculiX's 20-character reader width while retaining nonzero contributions.
- Pinned the local solver to one thread after this build returned incorrect results with two threads. [Build provenance and restrictions](verification/solver-runtime.md).
- Included camera controls explicitly because the dependency packaging filter omitted Three's examples directory; added an artifact-content check.
- Corrected the review label to reflect a completed independent analysis check.

## Current supported scope

One closed solid, homogeneous isotropic linear elasticity, quadratic tetrahedra or structured C3D8 bricks on compatible six-face planar blocks, translational/prescribed supports, total surface force and inward-positive pressure, CalculiX mesh-only or linear-static analysis export. Local refinement is geometry-directed. Mesh budgets, worker timeouts, hash checks, stale-write rejection and cancellation protect accepted artifacts.

The agent uses the installed Codex login and explicit application tools. It cannot invent missing material/load data or offer unsupported contact and nonlinear solves as completed work. Manual controls remain available without chat.

## Remaining release work and deferred features

External Python/Gmsh and GCC-dependent CalculiX runtimes must remain at their configured paths on this Mac. Runtime bundling, a clean second-Mac test, Developer ID signing and notarization are unverified. Assemblies/contact, shells, arbitrary complex all-hex or mixed meshes, nonlinear models, Abaqus export, result contours and automatic convergence/adaptation are outside this Option 1 pilot. Option 2 will add a separately validated results and convergence workflow.

Native face-list selection and section control visibility were verified. Viewport raycast picking and quality highlighting are implemented, but a complete manual interaction pass for every viewport control was not recorded.

## Icon and new-project update — 7 October 2026

Added a generated ivory/emerald mesh icon in the header, Dock and packaged Finder icon. Added New project to the toolbar and File menu with Cmd+N. It saves the current project, clears the viewport/chat/checks and startup project pointer, and returns to the reference-part/import landing screen. The focused worker tests pass, including blocking reset during an agent operation, byte-identical saved state and reopen after reset. Native toolbar/shortcut and startup recovery verification is recorded in `verification/new-project.json`. The meshing/export numerical implementation is unchanged.

## Brick and conversation update — 7 October 2026

Added a separate structured C3D8 path for compatible six-face CAD blocks, bilinear quad force integration, all six CalculiX pressure faces, quad viewport wireframes and brick Jacobian/reference checks. Five host/formatting tests and eleven numerical tests pass, including 22 actual CalculiX solves. Raw HTML in chat is escaped; common Markdown is rendered as readable headings, lists, tables and wrapped code. The header brand moves left while keeping vertical clearance from macOS window controls. [Scope and numerical evidence](ELEMENTS.md). Native packaged agent/brick evidence is recorded in `verification/native-brick.json`.

Native verification also identified a runtime-picker issue: macOS resolved a virtual-environment Python symlink to the base interpreter. Runtime selection now uses `noResolveAliases`, and native re-selection preserved the venv path. A stack trace showed Python startup stalling while opening its environment configuration in Documents; the packaged app now selects an app-owned copy of the already installed pinned environment in Application Support. No dependencies were downloaded and no macOS privacy permissions were changed.
