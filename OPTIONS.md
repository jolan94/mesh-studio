# Five product and architecture options

Prepared 6 October 2026. These are alternatives, not five simultaneous projects. Effort ratings are relative planning judgments; none of the new integrations has been executed.

Decision recorded 7 October 2026: the user selected **Option 1 first and Option 2 later**. Options 3–5 remain reference/fallback approaches. UI direction is still proposed; see [delivery plan](docs/plans/2026-10-07-option-1-delivery-plan.md).

All options retain AI chat, STEP inspection, user-visible mesh refinement, load/support selection, and CalculiX INP export as requirements. They differ in which existing platform owns the geometry/mesh and whether solver results drive refinement.

| Option | User experience and architecture | Refinement | Main benefit | Main cost or uncertainty | Fit |
|---|---|---|---|---|---|
| **1. Mesh & Load Studio — recommended first** | A new Mac app: chat + CAD/mesh viewport; Python Gmsh/OCCT worker; our deterministic region mapping and CalculiX deck writer. Reuse Part Studio's desktop/agent patterns. | Feature-based local sizing and bounded quality repair; follow-up prompts create checked revisions. | Closest to the requested experience; owns the whole import-to-INP workflow. | We must implement face picking, reliable boundary mapping, deck serialization, and Mac packaging. Medium effort. | Best MVP choice. |
| **2. Solve & Refine Studio** | Option 1 plus CalculiX execution, result inspection, and mesh-study controls in the app. | Solve, compare a declared response quantity, refine, repeat within a user budget. Local adaptation comes after a verified baseline study. | Strongest analysis workflow and later portfolio depth. | Result parsing, physically meaningful error criteria, solution singularities and repeated solve cost. High effort. | Best second phase. |
| **3. FreeCAD FEM Copilot** | Chat drives supported FreeCAD Python/document objects; FEM supplies much of the mesh/material/load/solver workflow. Initially a FreeCAD workbench or companion panel. | Existing FEM controls, region sizing and scripted remeshing. | Reuses a substantial existing analysis model and GUI. | FreeCAD document/state integration, version-specific APIs and external solver setup; embedding the full GUI in our Mac app is unproven. Medium effort. | Good if workflow reuse matters more than a small independent app. |
| **4. SALOME Meshing Copilot** | Chat controls GEOM/SMESH through Python; a separate worker owns meshing and group export; our adapter writes CalculiX analysis data. | Submeshes, alternative algorithms and more advanced preprocessing. | Strong meshing-oriented platform for a later expert product. | Official downloads reviewed list Linux/Windows, not a Mac package; a Linux worker introduces deployment work. INP group conversion needs verification. High effort for our Mac target. | Better for a later Linux/engineering-workstation edition. |
| **5. Multi-Mesher Studio** | A standalone app with separate Gmsh and Netgen adapters, a common analysis schema, and the same deck exporter/checker. | Generate bounded candidates with different engines/settings, compare quality/cost, let the user accept one. | More fallback choices and a visible comparison when one backend struggles. | Two native runtimes, cross-kernel region identity, adapter testing and packaging. More engines do not guarantee meshability. High effort. | Add only after one backend has measured failure cases. |

## Recommendation

Choose **Option 1**, with architecture that can grow into **Option 2**. Include materials, pressure, distributed force, fixed and prescribed-displacement supports in the first complete INP workflow. Use actual CalculiX runs for benchmark validation; an optional user-case check can report solver acceptance without introducing a complete results/adaptation product immediately.

Do not start with both Gmsh and Netgen, automatic assemblies/contact, arbitrary hex meshing, or a remote service. Each adds a separate validation burden before the basic user request works.

## What “AI understands the STEP” should mean

The worker reports measured bodies, bounds, topology, units, face types, cylindrical regions and import issues. The AI reasons over that report, the user's task, selected regions and optionally a preview. It cannot infer actual material, loads, manufacturing intent, contact or restraints from shape alone.

The user can identify a region by clicking or saying, for example, “the planar end face at minimum X.” The app highlights the match. A unique supported geometric selector can proceed; ambiguity prompts a focused question. Never assign a load to a guessed face silently.

## Evidence behind the alternatives

Gmsh-specific support and export limitations are in [the Gmsh research](docs/research/gmsh-feasibility.md). FreeCAD's documented FEM workflow includes materials, constraints, meshing and external solving ([official workbench documentation](https://raw.githubusercontent.com/FreeCAD/FreeCAD-documentation/main/wiki/FEM_Workbench.md)). SALOME offers multiple meshers ([official meshing overview](https://www.salome-platform.org/?page_id=374)); its extra INP export route involves conversion ([official export documentation](https://docs.salome-platform.org/latest/gui/SMESH/importing_exporting_meshes.html)). Netgen documents STEP/OCCT Python integration ([official tutorial](https://docu.ngsolve.org/latest/i-tutorials/unit-4.4-occ/occ.html)).

These establish plausible components. They do not establish that our proposed app, boundary-condition round trip, or packaging already works.
