# Script reference

All paths below are relative to the repository root. Keep the numbered folders and `paths.py` together.

## Entry points

| Script | Input | Output / behaviour |
| :--- | :--- | :--- |
| `quickstart.py` | One supplied or user-specified prepared STL | `output/quickstart/`: CSV, static three-view image, settings/version JSON; configurable with `--output` |
| `paths.py` | Repository location | Shared paths; `output_dir()` creates a per-script output folder |

## 1. Remeshing

The MATLAB source is included in `1_remeshing/Remeshing/`. Install MATLAB and its required toolboxes, then follow the [remeshing setup](../1_remeshing/Remeshing/README.md). These wrappers are optional for the supplied prepared meshes.

| Script | Purpose |
| :--- | :--- |
| `1_remeshing/Remeshing/setup_remeshing.m` | Checks MATLAB dependencies and installs MeshFix |
| `1_remeshing/Remeshing/remesh_batch.m` | Voxelizes, repairs and smooths raw STL meshes; writes a log for each batch |
| `1_remeshing/Remeshing/test_remeshing.m` | Checks the installation with a synthetic sphere |
| `1_remeshing/remesh_in_pycharm.py` | Watches the raw-input folder and calls MATLAB to write remeshed STLs and run logs; `--once` processes the current files and exits |
| `1_remeshing/remesh_human_head_in_pycharm.py` | The same remeshing-only workflow, with a default remeshing parameter of 60 |

The bird wrapper currently sets `PARA_DEFAULT = 40`. It is a tool for new raw inputs, not an automated replay of the specimen-specific preprocessing used to produce the released meshes. Use the already released meshes for the documented reproduction route; document the settings used for new raw scans.

## 2. Fitting

| Script | Default input | Output / behaviour |
| :--- | :--- | :--- |
| `2_fitting/fit_sphere.py` | `paths.FINCHES` | Interactive sphere fits; `output/fit_sphere/measurement_sphere_fitting_ALL.xlsx` |
| `2_fitting/fit_ellipsoid.py` | `paths.FINCHES` | Interactive ellipsoid fits; `output/fit_ellipsoid/measurement_ellipsoid_fitting_ALL.xlsx` |
| `2_fitting/fit_sphere_batch.py` | Carduelines, honeycreepers, Peromyscus | `output/fit_sphere_batch/`: workbook, images and failure log; folder-specific settings apply |
| `2_fitting/render_figures.py` | Batch-fitting workbook and meshes | Redraws inspection images from saved fit parameters |
| `2_fitting/fit_sphere_human_head_setting.py` | `paths.HUMAN` | Human-cranium fitting with its own search band and radius limits |
| `2_fitting/bounding_AABB.py` | A selected supplied skull | Axis-aligned bounding-box visualization |
| `2_fitting/bounding_OBB.py` | A selected supplied skull | Oriented bounding-box visualization |
| `2_fitting/check_orbit.py` | A prepared STL folder supplied with `--folder` | Separate fitting and inspection workflow; use `--results` to choose the output folder and `--no-show` to save images without opening windows |
| `2_fitting/fit_sphere_logged.py` | A prepared STL folder | Logged orbital fitter used by `check_orbit.py`; saves fit diagnostics and inspection images |

Settings are edited near the top of each original script (inside the main block for some scripts). They are not command-line flags unless explicitly documented.

Measurement exports omit remeshing-parameter columns. For the two Peromyscus examples, orbital fitting fields are blank and marked as not identifying an orbit. Diagnostic figures can still show the fitted sphere to illustrate this limitation. The figure script's internal `figure_cache` retains the diagnostic fits needed to redraw those figures; it is not a table of orbital measurements.

## 3. Statistics

| Script | Input | Purpose |
| :--- | :--- | :--- |
| `3_statistics/correlation.py` | `data/Dataset.xlsx` | Pearson/Spearman summaries and scatter plots |
| `3_statistics/correlation_combined.py` | `data/Dataset.xlsx` | Correlation tables involving the ellipsoid axes |
| `3_statistics/correlation_specific.py` | `data/Dataset.xlsx` | Selected regression and its model summary |
| `3_statistics/modelling.py` | `data/Dataset_training.xlsx` | Multiple linear regression of curvature on dimensions; training-data plot |

## 4. Bilateral fits

| Script | Purpose | Output |
| :--- | :--- | :--- |
| `4_two_orbits/two_orbit.py` | Fits the opposite orbit and draws the pair | `output/two_orbit/`, including `two_orbit_results.csv` |
| `4_two_orbits/verify_fit.py` | Headless orbital fitter and standalone batch diagnostics | `output/verify_fit/verify_fit_results.csv` by default |

`verify_fit.py` also accepts mesh-folder arguments and an optional output CSV path. It uses its own finch defaults and does not automatically inherit `fit_sphere_batch.py`’s folder overrides.

## 5. Figures and animation

| Script | Options | Output |
| :--- | :--- | :--- |
| `5_figures/figure.py` | `--only 4,9,S2`, `--eps`, `--refit` | `output/figure/figures/`, with a separate measurement cache |
| `5_figures/demo_animation.py` | Settings in the file | `output/demo_animation/`: GIF, MP4 and frames |

The figure builder uses prepared meshes plus the included [figure inputs](../data/figure_inputs/README.md). It is not a converter for the supplied manuscript PDFs.

## 6. Verification

`6_verification/verify_all.py` recomputes measurements and compares them with encoded expected values. Configuration is at the top of the file. It writes reports, tables and workbooks under `6_verification/output/verify_all/`. See the [reproduction guide](REPRODUCE.md) for what a passing report establishes.

## Documentation

The Markdown guides are the editable source. The corresponding HTML guides are generated with `tools/build_docs.py` using the Python `Markdown` package. The landing page is `docs/index.html`; `docs/assets/` contains its media and styling. No web framework or build service is needed to read it.

[Overview](../README.md) · [Start here](START_HERE.md) · [Reproduce](REPRODUCE.md)
