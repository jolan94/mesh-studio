# Running Mesh & Load Studio

The current build is a local Apple Silicon pilot. Open `app/dist/mac-arm64/Mesh & Load Studio.app` on this Mac, or run `npm start` from `app`. Development uses the isolated project Python environment. The packaged app on this Mac uses a copy of that pinned environment at `~/Library/Application Support/step-mesh-studio/runtimes/python-3.12-gmsh-4.15.2/bin/python`, plus the project-local CalculiX executable and your installed Codex. Runtime settings let you choose each executable. Chat requires an existing ChatGPT login in Codex; manual preparation remains available when chat is disconnected.

A project is a folder containing immutable `source.step`, imported geometry, accepted mesh revisions, setup, conversation, exports and optional solver-check artifacts. Changes autosave to `project.json`. Use Open project to reopen this folder. Do not edit accepted geometry/mesh files directly: hashes are verified before using them.

## Reproduce the Python and desktop runtime

From the project root, create `.venv` with Python 3.12 and install the pinned `app/requirements.txt` using uv or pip. From `app`, run `npm ci`, then `npm start`. Set Python, Codex and Node executable paths in Runtime settings. The native picker preserves Python virtual-environment symlinks; resolving one to the base interpreter would lose the meshing dependencies. If macOS stalls Python while reading its environment in Documents, keep a copy of the pinned environment in the app-owned Application Support directory and select its `bin/python`. No privacy setting changes are required for this local configuration. There is no app-owned API key or token copy. `app/runtime.json` is machine-specific and ignored; the packaged app includes the configured paths for this developer Mac.

## Reproduce the solver

The solver uses existing Clang, GCC 15 and Apple Accelerate. Download these official archives into `runtime/src`:

- `https://www.dhondt.de/ccx_2.23.src.tar.bz2` as `ccx.tar.bz2`
- `https://www.netlib.org/linalg/spooles/spooles.2.2.tgz` as `spooles.tgz`
- `https://github.com/opencollab/arpack-ng/archive/refs/tags/3.9.1.tar.gz` as `arpack.tgz`

Run `.venv/bin/python app/scripts/build_arpack.py`, followed by `.venv/bin/python app/scripts/build_solver.py`. Both scripts verify pinned archive hashes. Set `runtime/bin/ccx_2.23` in the app. See [runtime verification](verification/solver-runtime.md). The pilot pins solver execution to one thread.

## Use the app

1. Use **New project** in the toolbar or File menu (**⌘N**) to return to the start screen. The current project is saved and can be reopened. Import a STEP and create a new empty `.meshstudio` project folder, or use an original reference part.
2. Check the normalized millimeter dimensions. Unsupported assemblies/open surfaces remain inspection-only.
3. Pick faces in the viewport or measured face list and name them when useful. The selected region becomes chat context.
4. Set global target size, optional local target and transition distance; generate quadratic C3D10 tetrahedra. Element family also offers C3D8 bricks for compatible six-face blocks; use global size and clear local refinements before switching. See [element scope](ELEMENTS.md).
5. Enter explicit E in MPa and nu. Add translational supports, prescribed displacements, total force vectors in N or inward-positive pressure in MPa.
6. Check mesh-only or analysis INP. An analysis deck needs material, nonzero loads and sufficient rigid-body restraint. Check with CalculiX is optional; it checks execution and reaction balance, not convergence.
7. Export through the native save dialog. Codex can also write checked exports inside the project `exports` folder. Each export has a hash/report; accepted meshes are preserved on failed/cancelled candidates.

A full chat example: “Inspect this part. Mesh at 4 mm, refine the xmax face to 2 mm with an 8 mm transition. Use E=210000 MPa and nu=0.3, fix xmin in XYZ, apply 750 N in +X on xmax. Check with CalculiX and export prepared.inp.” Use this only where those properties and regions describe the intended case. Ambiguous end faces or missing physics require clarification.

## Verification and packaging

`cd app && npm test` exercises the real worker, revision integrity, stale writes, failure recovery, save/reopen and cancellation. `npm run test:kernel` performs actual geometry/INP/solver benchmarks. `node scripts/agent-check.cjs` and `node scripts/agent-followup.cjs` use the real signed-in agent and consume account usage. `npm run pack` uses the installed Electron distribution and never publishes.

This `.app` is locally ad-hoc signed, not Developer ID signed/notarized. Python/Gmsh and the GCC-dependent CalculiX runtime are external. A second Mac and standalone runtime bundling are not verified. Keep the project/runtime folders available; moving them requires updating executable paths. Distribution signing, portable runtimes and broader CAD coverage remain release work. Option 2 results/convergence and Abaqus export are deferred.
