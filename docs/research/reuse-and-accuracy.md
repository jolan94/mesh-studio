# Reuse and accuracy: FreeCAD, SALOME and our app

Reviewed 7 October 2026. Documentation research and design judgments only; no comparative runtime results.

## Can we build our interface on existing software?

Yes. There are three different levels of reuse:

1. **Kernel/API reuse:** our own desktop interface calls Gmsh/OCCT and a solver. This is selected Option 1. We do not write a tetrahedral meshing algorithm.
2. **Platform reuse:** our interface sends structured commands to a FreeCAD or SALOME worker, which owns its document, geometry and analysis/mesh objects. This is plausible but the chosen runtime/GUI dependencies need a spike.
3. **Native extension:** add a chat workbench/panel inside FreeCAD or SALOME. This reuses their viewport and selection most directly; it produces an extension of that host application.

A bespoke UI can use a backend platform. It is not necessary to display that platform's existing interface. However, copying only a few functions may import assumptions about its document model, preferences, installed tools and runtime. Reuse through supported APIs is generally easier to keep up to date. Any reused source requires its actual licenses and attribution.

## FreeCAD: strongest alternative for this workflow

FreeCAD FEM documents a complete preprocessing/solving workflow. Its Python tutorial demonstrates analysis objects, material/support/load setup, meshing and CalculiX execution. Gmsh integration exposes mesh settings; therefore wrapping FreeCAD does not necessarily introduce a different underlying mesh engine.

Sources: [official FEM workbench](https://raw.githubusercontent.com/FreeCAD/FreeCAD-documentation/main/wiki/FEM_Workbench.md), [official Python tutorial](https://raw.githubusercontent.com/FreeCAD/FreeCAD-documentation/main/wiki/FEM_Tutorial_Python.md), [official Gmsh integration](https://raw.githubusercontent.com/FreeCAD/FreeCAD-documentation/main/wiki/FEM_MeshGmshFromShape.md).

**Design judgment:** A FreeCAD extension could reduce our initial selection, setup and deck-writing work. A separate app backed by FreeCAD trades that reuse for a larger document/runtime integration. We should use its documented workflow as a reference and comparative baseline before committing substantial custom exporter work. Its tutorial is older than current development: pin and verify actual APIs instead of treating snippets as current runnable code.

## SALOME: strong preprocessing platform, more integration work here

SMESH documents mesh generation, modification, groups, quality controls and Python access. The official downloads reviewed list Linux/Windows, without a macOS package. A separate Linux worker is possible, but requires explicit deployment and geometry-transfer design. SMESH's mesh/group output is not by itself our complete CalculiX load/material/step deck.

Sources: [official mesh introduction](https://docs.salome-platform.org/latest/gui/SMESH/index.html), [Python interface](https://docs.salome-platform.org/latest/gui/SMESH/smeshpy_interface.html), [exports](https://docs.salome-platform.org/latest/gui/SMESH/importing_exporting_meshes.html), [downloads](https://www.salome-platform.org/?page_id=2430).

**Design judgment:** SALOME is worth reconsidering for complex submeshing, multi-body or an engineering-workstation edition. It is not the simplest starting dependency for the selected Mac app.

## Would accuracy be better?

There is no benchmark yet that establishes one route is more accurate. Mesh conformity, element formulation/order, local resolution, material, boundary conditions and solver settings determine the response. The user interface can improve accuracy indirectly by helping a user define and inspect those inputs correctly.

With equivalent geometry, algorithm/settings, element order, analysis deck and solver, changing only the UI does not inherently improve the numerical model. Different defaults, geometry cleanup, load distribution or region mapping can produce different results; compare the actual exported files and response quantities within stated tolerances.

Mature platforms offer existing setup and inspection workflows. That can reduce our integration mistakes, but does not establish every model is correct. Our greatest early risks are C3D10 node ordering, load-face direction, missing regions after remeshing, incorrect unit scaling and load distribution. Validate those before claiming parity.

Part Studio currently checks CAD geometry; it does not provide a structural simulation accuracy baseline. Compare this meshing project against analytic examples and an established FEM workflow, rather than against Part Studio's CAD-generation results.

## Proposed reference comparison in the feasibility phase

Use three original fixtures: axial bar, cantilever and pressure-loaded block. Keep geometry, material, load/support regions and solver version fixed. Compare our pipeline with a configured FreeCAD/Gmsh/CalculiX reference where available.

Record mesh parameters, elements/nodes, region membership/area, applied resultant/moment, reactions, selected displacement and energy measures, and all warnings. Different meshes require a refinement study; do not compare only visually attractive surfaces or raw node counts.

If custom deck export or region mapping remains unreliable, explicitly review the FreeCAD-worker alternative. Keep the public project/analysis schema separate from backend objects so that a fallback does not require redesigning chat and the workspace.
