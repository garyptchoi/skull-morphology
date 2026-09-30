# MATLAB remeshing

This folder contains the MATLAB batch function and the helpers used by the Python remeshing scripts. It voxelizes raw skull meshes, attempts to close handles and holes, smooths the surface, and writes STL files for fitting.

You can skip this step when using the prepared meshes in `data/`.

## Requirements

- **MATLAB R2021a or later**, because the topology-repair routine uses [`cyclebasis`](https://www.mathworks.com/help/matlab/ref/graph.cyclebasis.html).
- **Image Processing Toolbox** for filling, connected components and skeletonization.
- **Statistics and Machine Learning Toolbox** for the distance calculations used in topology repair.
- Internet access for the first MeshFix download. An offline installation is also possible.

The supplied voxelizer binaries cover 64-bit Windows, Linux, Intel macOS and Apple silicon macOS. The C source is included for rebuilding if a binary does not load in your MATLAB version. Rebuilding requires a C compiler supported by MATLAB.

## Set up once

In MATLAB, start in the repository root and run:

```matlab
cd('1_remeshing/Remeshing')
setup_remeshing
test_remeshing
```

`setup_remeshing` checks the toolboxes and voxelizer, then downloads the MeshFix executable for your platform from a fixed revision of the official iso2mesh repository. `test_remeshing` runs a small synthetic-sphere test; it does not use or alter the study meshes.

If MATLAB reports an invalid MEX file, run:

```matlab
mex -setup C
setup_remeshing('RebuildMex', true)
```

For an offline installation, obtain the matching MeshFix binary from the [pinned iso2mesh folder](https://github.com/fangq/iso2mesh/tree/4a0ca5b65d5d292b83b40fd0fdcb742625e573a6/bin), place it in `code/iso2mesh/bin/`, and run `setup_remeshing('DownloadMeshFix', false)`. On Windows, rename `meshfix_x86-64.exe` to `meshfix.exe`. MeshFix is a separate executable, despite the `.mex*` extensions used on macOS and Linux.

## Use the Python workflow

Put raw scans in `1_remeshing/dataset_CT/`. Install the Python requirements, then run this command from the repository root:

```bash
python 1_remeshing/remesh_in_pycharm.py --once
```

The wrapper finds this MATLAB folder automatically. It accepts STL, PLY, OBJ and OFF inputs, converts them to STL when needed, and writes remeshed STL files and run logs. It stops after remeshing. It uses MATLAB Engine when available, otherwise `matlab -batch`. If MATLAB is not on your system path, pass `--matlab` with the full path to the MATLAB executable.

`--overwrite` refreshes the staged raw inputs and remeshes them again. MATLAB errors and missing output meshes return a nonzero exit status. A successful process still needs a check of the output geometry.

`remesh_in_pycharm.py` handles both bird and human raw meshes and uses a default remeshing parameter of 60. Fitting is a separate operation in `2_fitting/`. To inspect a prepared mesh after remeshing, run:

```bash
python 2_fitting/check_orbit.py --folder 1_remeshing/dataset_remeshed --results 2_fitting/output/check_orbit --no-show
```

The human fitting script in `2_fitting/` reproduces the released human fits with the paper's 10–50% search band and 2–60 mm radius range.

For specimen-specific parameters, create `1_remeshing/params.csv`:

```csv
filename,para,reason
specimen.stl,60,chosen after inspecting the surface
```

Use the `.stl` filename here even when the original scan is PLY, OBJ or OFF. The Python wrapper uses `PARA_DEFAULT = 60` for files without an override. Choose the parameter by inspecting the resulting surface; these defaults do not reproduce every specimen's original preprocessing.

## Use MATLAB directly

From `1_remeshing/Remeshing/`:

```matlab
remesh_batch('../dataset_CT', '../dataset_remeshed', '../params.csv', ...
    'MeshFix', true, 'Rescale', false, 'Seed', 0)
```

Direct MATLAB input must be STL. Without a parameter CSV, `remesh_batch('../dataset_CT', '../dataset_remeshed')` uses `para = 60`. MATLAB and the Python wrapper use the same default. A parameter CSV can override it for individual specimens.

To try the original scan-derived surface included for Fig. 1, run this after setup from `1_remeshing/Remeshing/`:

```matlab
remesh_batch('../../data/figure_inputs/raw_meshes', ...
             '../../output/raw_mesh_test', '', 'Seed', 0)
```

This uses `para = 60` and writes `P2.InornataA_p60.stl`, `remeshing_log.csv` and `remeshing_settings.txt` into `output/raw_mesh_test/` at the repository root. Check the new STL for boundary and non-manifold edges, connected components and surface distortion before interpreting its fits. A watertight surface alone does not establish anatomical accuracy. Use a new output folder for an independent rerun, since existing meshes are skipped unless `Overwrite` is enabled.

| Option | Default | Purpose |
| :--- | :--- | :--- |
| `MeshFix` | `true` | Repair meshes that fail the Euler check |
| `Rescale` | `false` | Apply the optional ICP alignment and rescaling step |
| `RescaleMode` | `'uniform'` | Use `'nonuniform'` for separate axis scale factors |
| `Overwrite` | `false` | Skip existing outputs unless explicitly enabled |
| `Seed` | `0` | Reset the random generator before each specimen |
| `Threads` | `[]` | Use MATLAB's current thread setting |

New working outputs retain the `<specimen>_p<para>.stl` format expected by the Python wrappers. The cleaned filenames of the released meshes in `data/` are unchanged. Each run writes `remeshing_log.csv` and appends its settings to `remeshing_settings.txt` in the output folder. Check the log for failed specimens and inspect the surfaces before fitting. Remeshing does not establish anatomical orientation.

The same seed makes runs less dependent on processing order; identical results across MATLAB versions or platforms are not guaranteed.

## Included files

| File or folder | Role |
| :--- | :--- |
| `remesh_batch.m` | Batch entry point called by Python |
| `setup_remeshing.m` | Dependency checks, MEX rebuild and MeshFix installation |
| `test_remeshing.m` | Small installation smoke test |
| `code/voxelization/` | Voxelization, topology repair and Skeleton3D |
| `code/mesh/` | Laplacian smoothing and supporting matrix routines |
| `code/stlTools/` | STL reading and writing |
| `code/iso2mesh/` | MeshFix interface and supporting I/O |
| `code/natsortfiles/` | Natural filename sorting |

The source was taken from the supplied remeshing archive. The primary function name in `voxelelize_genus.m` now matches its filename, and the `conncomp` fallback receives a MATLAB graph object. The voxelization and smoothing parameters are unchanged.

Third-party credits and licenses are recorded in [THIRD_PARTY.md](https://github.com/kaikwanlau/skull-morphology/blob/main/1_remeshing/Remeshing/THIRD_PARTY.md). This is a selected dependency set; unrelated toolboxes, old demos, raw scans and workspace files are excluded.
