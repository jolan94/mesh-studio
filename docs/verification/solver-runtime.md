# CalculiX runtime verification

Pinned source: CalculiX 2.23, SHA-256 `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`; SPOOLES 2.2, SHA-256 `a84559a0e987a1e423055ef4fdf3035d55b65bbe4bf915efaa1a35bef7f8c5dd`; serial ARPACK-ng 3.9.1, SHA-256 `f6641deb07fa69165b7815de9008af3ea47eb39b2bb97521fbf74c97aba6e844`.

Built on this Apple Silicon Mac using existing GCC 15, Clang and Apple Accelerate. SPOOLES and serial ARPACK are linked statically; the executable still uses the installed GCC runtime libraries. Reproduction scripts: `app/scripts/build_arpack.py`, then `app/scripts/build_solver.py` after fetching the named upstream archives into `runtime/src`.

The build needs a narrow upstream compatibility patch: `readnewmesh()` returns void and must use `return;`; the pointer-returning `genratiomt()` retains `return NULL;`. Makefile library paths are passed quoted because this workspace contains a space. Compile all objects using the same ARPACK flags; reusing previously compiled objects without those flags produces missing-symbol errors.

A real cantilever exposed incorrect results with this local build using two solver threads. The same exact INP at one thread produced balanced reactions and the analytic displacement. The app therefore pins the CalculiX process to one CPU/thread (`NUMBER_OF_CPUS`, `OMP_NUM_THREADS`, and CCX result/stiffness/equation-solver thread controls). This is a tested runtime restriction, not a diagnosed upstream universal defect. Parallel CalculiX runs are not supported by this pilot.

A temporary Homebrew ARPACK attempt depended on MPI; it was removed after the project-local serial build worked. The temporary CalculiX tap was also removed. Existing Homebrew formulae were not upgraded.

Independent exported-deck references and analytic/reaction results are recorded in `kernel-results.json`; successful Gmsh generation alone does not count as a solver check.

The exporter formats every floating input field within CalculiX's 20-character limit (`cloads.f` reads the load using `textpart(3)(1:20)`). It retains the highest precision that fits, rather than truncating an exponent. Tiny nonzero consistent nodal contributions remain in the deck.

Reaction checks follow the official 2.23 manual's “Output of forces”: `RF` is the sum of loading and reaction forces. The checker subtracts applied nodal contributions on constrained directions before summing reactions/moments. Pressure contributions use the same oriented quadratic surface shape functions, including midsides. A real curved-bore pressure case with a intersecting fixed bottom face and near-zero net load passes this correction. Balance tolerance scales with applied load magnitudes, including self-equilibrating pressure, rather than only the net resultant. Source: https://www.dhondt.de/ccx_2.23.pdf .
