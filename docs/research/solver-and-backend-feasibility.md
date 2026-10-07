# Solver and alternative-backend feasibility

Researched 6 October 2026 against primary documentation. No software was installed or run. `ccx` and `gmsh` were not found on the current shell PATH; that does not establish they are absent from other environments.

## CalculiX target

The official site lists CalculiX 2.23 and notes its Abaqus-derived input conventions. This is not a guarantee of complete Abaqus compatibility. The manual documents C3D10 tetrahedra, displacement constraints, distributed loads and consistent-unit requirements. Proposed first structural export: quadratic tetrahedra and linear elasticity, with version-pinned validation against the selected solver binary. Density becomes necessary when supporting gravity.

Sources: [official CalculiX site](https://www.dhondt.de/), [2.23 manual](https://www.dhondt.de/ccx_2.23.pdf), especially Units, Element Types, *BOUNDARY and *DLOAD. The manual also documents node/face numbering; implement export mapping from the pinned version rather than assumptions.

## FreeCAD option

FreeCAD's documented FEM workflow combines geometry, materials, constraints, meshing and external solving. Its documentation includes fixed/displacement constraints, force/pressure loads, Gmsh/Netgen meshing and CalculiX. This supports evaluating a workbench/companion integration. It does not prove a headless or embedded Mac workflow for this project.

Sources: [official FEM workbench](https://raw.githubusercontent.com/FreeCAD/FreeCAD-documentation/main/wiki/FEM_Workbench.md), [official dependency setup](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/FEM_Install.md).

## SALOME option

SMESH supports several meshers. Extra INP output can pass through Gmsh; conversion and named-region preservation need a spike. The reviewed download selector lists Linux and Windows packages and no macOS package. A Linux worker is therefore a proposal, not an already-working Mac distribution route.

Sources: [meshing overview](https://www.salome-platform.org/?page_id=374), [formats and conversion](https://docs.salome-platform.org/latest/gui/SMESH/importing_exporting_meshes.html), [official downloads](https://www.salome-platform.org/?page_id=2430).

## Netgen option

Netgen documents a Python OCCT wrapper, STEP import and mesh generation. It requires OCC-enabled support. Whether its chosen distribution, output mapping and quadratic-element export meet this Mac/CalculiX workflow remains untested.

Source: [official OCCT tutorial](https://docu.ngsolve.org/latest/i-tutorials/unit-4.4-occ/occ.html).

## Abaqus later

Abaqus/CAE's input reader supports a documented subset of keywords and elements and may ignore unsupported content. Plan a separate adapter and licensed import/solve checks before claiming analysis compatibility. A mesh that imports is insufficient evidence that loads and supports survived.

Source: [official model-import documentation](https://docs.software.vt.edu/abaqusv2025/English/SIMACAECAERefMap/simacae-t-impinputfilereader.htm).

## Proposed integration experiments

1. Determine an Apple Silicon CalculiX executable/build route and pin the tested version; do not assume the site's Linux binaries run on macOS.
2. Export a constrained block with known directional load. Reparse the written deck independently, execute CalculiX, and compare displacement and reactions with an analytic reference.
3. Test quadratic tetrahedron node ordering and every pressure face. Verify both total force and moment; a wrong face can remain syntactically valid.
4. Repeat after local refinement; compare named region area/location and resultant load even though node IDs changed.
5. Declare which decks are merely structurally checked and which were actually solved. Preserve logs and response measurements.
6. Audit dependency licenses/source notices before choosing a redistribution model. CalculiX's site links GPLv2; final packaging decisions require the actual pinned components' license files.

## Access note

The Agent Reach Jina-reading route failed DNS resolution in the restricted shell. Research continued through the available web tool using primary sites. Several guessed HTML documentation URLs were inaccessible; the linked official CalculiX PDF and accessible official backend pages provided the evidence used here.
