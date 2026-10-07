# Element families

## C3D10 quadratic tetrahedra

The existing general single-solid path remains the default. Delaunay/HXT algorithms and local CAD-face sizing are available. Accepted legacy projects without an explicit family are interpreted as C3D10.

## C3D8 linear bricks

Choose **Mesh & refine → Element family → C3D8 · linear brick**, or ask Codex for C3D8. The worker builds a structured transfinite hexahedral mesh, not a relabeled tetrahedral mesh. It requires one closed solid with six planar four-sided faces, twelve straight edges and eight corners. Opposite edges share subdivision counts; the longest edge in each compatible direction sets the count from global target size. Counts are rounded up and can produce smaller cells than the requested target.

This path uses a global grid. Clear existing local refinements explicitly before switching. Local face grading, arbitrary complex all-hex meshing, swept holes, external partitioning and mixed-element meshes are not supported. Unsupported requests leave the accepted mesh and physics intact; the app never silently falls back to tetrahedra. A holed plate needs a separate swept/partitioned meshing workflow before it can receive an all-brick mesh.

Loads, constraints, region naming, revision history, solver checks and INP export support both families. Brick quadrilateral faces render without artificial triangle diagonals. Face numbering uses CalculiX's six brick faces. Distributed forces use bilinear quadrilateral integration; pressure resultants, moments and forces on restrained DOFs are accounted for. The independent INP parser checks connectivity, sampled brick Jacobians, exterior face references and rigid-body restraint.

C3D8 uses full integration. It can be too stiff in bending and for nearly incompressible material behavior; element choice alone does not guarantee greater accuracy. The application warns about bending and does not claim solution convergence. C3D20, reduced-integration formulations, shells and beams need their own verification before being added.

## Verification

Five host/formatting tests and eleven numerical tests passed. The numerical suite includes 22 actual CalculiX runs: the previous tetrahedral cases, two brick axial grids, six brick pressure directions, and pressure intersecting a restrained boundary. Brick node order is compared directly against Gmsh's INP writer. Tests also reject incompatible geometry, local brick refinement and an inverted brick; changing family preserves physics and selected revisions.

See [machine-readable numerical evidence](verification/kernel-results.json), [host log](verification-host-elements.log) and [numerical log](verification-elements.log). Axial C3D8 examples are approximately 1.22% and 0.94% from FL/EA for 4 mm and 2 mm global targets; their fully fixed end locally suppresses Poisson contraction. These are benchmark examples, not a general accuracy guarantee.

## Primary references

- [Gmsh 4.15.2 documentation](https://gmsh.info/doc/texinfo/gmsh.html): transfinite volume meshing and recombined quadrilateral surfaces.
- [CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf): C3D8 formulation, limitations, node order and face numbering.
