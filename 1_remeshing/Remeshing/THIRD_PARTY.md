# Remeshing dependencies and credits

The MATLAB files in this folder were selected from the supplied `MATLAB副本.zip` archive. They are the dependencies of `remesh_batch.m`, including its optional ICP rescaling step. The unrelated geometry toolboxes, experiments, sample meshes and workspace files from that archive are not included.

The project's Apache 2.0 license does not replace the licenses of these dependencies. Ordinary comments have been removed from the MATLAB source; original comment text, including author credits and source references, is preserved in `THIRD_PARTY_NOTICES.txt`. License files are retained alongside the relevant code.

| Component | Author / source | License or notice |
| :--- | :--- | :--- |
| `code/mesh/` | [gptoolbox](https://github.com/alecjacobson/gptoolbox), Alec Jacobson and contributors; individual notices also credit Denis Zorin and Daniele Panozzo | Upstream Apache 2.0 license in `code/mesh/LICENSE.Apache-2.0`; original copyright notices in `THIRD_PARTY_NOTICES.txt` |
| `code/iso2mesh/` | [iso2mesh](https://github.com/fangq/iso2mesh), Qianqian Fang | Upstream `code/iso2mesh/COPYING.txt`; the JSONLab helpers `jsonopt.m` and `varargin2struct.m` also permit the included `LICENSE_BSD.txt` terms |
| MeshFix executable | [MeshFix](https://github.com/fangq/meshfix), Marco Attene | Downloaded separately by setup from iso2mesh revision `4a0ca5b65d5d292b83b40fd0fdcb742625e573a6`; see upstream source, license and citation information |
| `code/stlTools/` | [stlTools](https://www.mathworks.com/matlabcentral/fileexchange/51200-stltools), Pau Micó, with contributions credited to Sven Holcombe, Grant Lohsen, Adam H. Aitkenhead, Francis Esmonde-White and Eric Johnson | `code/stlTools/license.txt`, `code/stlTools/readme.txt` and original notices |
| `polygon2voxel.m` and `polygon2voxel_double.*` | [Polygon2Voxel](https://www.mathworks.com/matlabcentral/fileexchange/24086-polygon2voxel), Dirk-Jan Kroon; supplied MATLAB wrapper includes later modifications | `code/voxelization/license-polygon2voxel.txt`; C source accompanies the supplied platform binaries |
| `code/voxelization/Skeleton3D/` | Philip Kollmannsberger; based on the thinning algorithm of Lee, Kashyap and Chu (1994) | Original `license.txt` and `readme.txt` in that folder |
| `code/natsortfiles/` | Stephen Cobeldick | Original `license.txt` in that folder |
| `icp_matlabcentral.m` | [Iterative Closest Point](https://www.mathworks.com/matlabcentral/fileexchange/27804-iterative-closest-point), Martin Kjer and Jakob Wilm, Technical University of Denmark (2012) | `code/license-icp.txt` and original notices in `THIRD_PARTY_NOTICES.txt` |
| `compute_edges.m`, `check_face_vertex.m` | Gabriel Peyré | Original 2004 and 2007 copyright notices in `THIRD_PARTY_NOTICES.txt` |

The supplied voxelization code also credits Jianxiong for hole-filling changes and F. Moreno-Noguer for reversing the coordinate transformation. Those notices are preserved in `THIRD_PARTY_NOTICES.txt`.

## Changes made for this repository

- Kept the batch function's voxelization, smoothing and optional rescaling calculations.
- Added automatic loading of the bundled helper folders and an actionable missing-MEX message.
- Matched the function name in `voxelelize_genus.m` to its filename.
- Changed the fallback `conncomp(Adj)` call to `conncomp(graph(Adj))`, so it uses MATLAB's graph API without the full gptoolbox on the path.
- Removed explanatory comments from `.m` files while retaining their original text separately.
- Added setup and synthetic-sphere test functions. MeshFix downloads occur only during setup.

The scratch demonstration in the original archive refers to local paths and contains an incomplete STL-writing statement. The supported entry point here is `remesh_batch.m`.
