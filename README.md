# Robust parametric estimation of avian cranial morphology

Code and data for the paper *Robust Parametric Estimation of Avian Cranial Morphology* by **Kaikwan Lau and Gary P. T. Choi**.

The Python scripts estimate skull dimensions, orbital radius and neurocranial shape from prepared 3D skull meshes. The repository includes the study datasets, fitting scripts, statistical analyses and instructions for using the code with other specimens.

[Read the paper](https://arxiv.org/abs/2511.06426) · [Start with one skull](docs/START_HERE.md) · [Use your own data](docs/START_HERE.md#use-your-own-skulls) · [Reproduce the paper](docs/REPRODUCE.md)

<p align="center"><a href="docs/assets/demo.mp4"><img src="demo.gif" width="800" alt="A real skull mesh progresses through a bounding box, curvature-based orbit selection, a fitted sphere and a braincase ellipsoid." /></a></p>

<p align="center"><sub>18.8-second method overview · <a href="docs/assets/demo.mp4">MP4 version</a> · <a href="docs/assets/tutorial.mp4">7:09 guided tutorial</a></sub></p>

## Documentation

| Task | Guide |
| :--- | :--- |
| Understand the method | The animation above and the measurements described below |
| Analyse your own skull meshes | [Biologist’s guide](docs/START_HERE.md): installation, an example and input requirements |
| Prepare raw scans | [MATLAB remeshing setup](1_remeshing/Remeshing/README.md): dependencies and batch processing |
| Reproduce the study | [Reproduction guide](docs/REPRODUCE.md): datasets, analyses, figures and numerical checks |

After downloading the repository, open **`docs/index.html`** in a browser for the project website, including both videos and illustrated explanations of the measurements. The website also works offline.

## Measurements

| Skull size | Orbit | Neurocranium |
| :--- | :--- | :--- |
| Axis-aligned length, width and height | A sphere fitted to a connected concave surface patch | An axis-aligned ellipsoid fitted to a connected convex patch |
| `length_x`, `width_y`, `height_z` | Radius `r` and curvature `1/r` | Semi-axis lengths `a`, `b`, `c` |
| Mesh coordinates need the intended anatomical orientation | A numerical fit still needs anatomical inspection | Semi-axes describe the fitted geometry, not direct brain measurements |

The scripts require prepared, anatomically oriented meshes. The default fitting settings were selected for the finch dataset; other skull shapes may require different settings and should be checked visually.

## Run an example

Download and unzip this repository using **Code → Download ZIP**, or clone it. With **Python 3.12**, open a terminal in the repository folder and create a virtual environment:

```bash
python -m venv .venv
```

Activate it with `source .venv/bin/activate` on macOS/Linux, or `.venv\Scripts\activate.bat` in Windows Command Prompt. On macOS/Linux, use `python3` for the first command if `python` is unavailable.

```bash
python -m pip install -r requirements-quickstart.txt
python quickstart.py
```

This fits an orbital sphere to the supplied **`G.DifficilisA.stl`** specimen and saves measurements, a three-view inspection image, and the settings and software versions in **`output/quickstart/`**. The example runs without MATLAB or an interactive 3D window.

For the full workflow, install `requirements.txt` and follow the [biologist’s guide](docs/START_HERE.md). The orbital example does not perform the ellipsoid fit or the paper’s full analysis.

## Datasets

The main analyses use 100 skulls of Darwin’s finches and their relatives. Applicability to other skulls is examined in Supporting Information Section S4.

| Dataset | Skulls | Use in the study |
| :--- | ---: | :--- |
| Darwin’s finches and relatives | 100 | Skull measurements and statistical analyses |
| Hawaiian honeycreepers and cardueline relatives | 51 (42 + 9) | Application of the finch fitting settings to additional bird skulls |

Two rodent skulls and four human crania are included as exploratory examples. The rodent fits did not identify the orbits. The human fits used adjusted settings, and none met both S4 quality criteria. See [data sources and scope](data/README.md) for details.

The fitting and statistical analyses start from the released prepared meshes. The photograph, original scan-derived skull surface and two earlier-remeshed skulls used in Fig. 1 and Fig. S1 are also included; see [figure inputs and sources](data/figure_inputs/README.md).

## Repository structure

| Folder | Purpose |
| :--- | :--- |
| [`data/`](data/) | Prepared meshes and the three released measurement workbooks |
| [`1_remeshing/`](1_remeshing/) | Raw-mesh preparation with the included MATLAB code; MATLAB and its required toolboxes must be installed |
| [`2_fitting/`](2_fitting/) | Dimensions, orbital spheres and neurocranial ellipsoids |
| [`3_statistics/`](3_statistics/) | Correlations and the curvature regression model |
| [`4_two_orbits/`](4_two_orbits/) | Bilateral fits and diagnostic outputs |
| [`5_figures/`](5_figures/) | Paper figures and the overview animation |
| [`6_verification/`](6_verification/) | Refit meshes and compare against encoded manuscript values |

`paths.py` defines the data paths. Generated results go into `output/` folders; remeshing uses its own working folders. The [script reference](docs/REFERENCE.md) lists each script’s inputs and outputs.

## Before interpreting a fit

- Use prepared triangular STL meshes in **millimetres**, with **beak at −x, posterior at +x, and dorsal direction +z** for the bird workflow. The fitting scripts do not establish anatomical orientation for arbitrary inputs.
- The default orbital search band and radius limits were selected for the finch dataset. Other taxa may need different settings; the supplied human examples already use different limits.
- Inspect the selected points and fitted surface. The SI Section S4 screen of **at least 40 inliers and RMS/radius ≤ 0.10** flags fits for review; it is not an automatic acceptance filter in `fit_sphere_batch.py`, nor proof that a fit is anatomically correct.
- The regression is an empirical model within the study’s sampled size range. Do not treat it as a universal predictor across taxa.

## Cite this work

Kaikwan Lau and Gary P. T. Choi. *[Robust Parametric Estimation of Avian Cranial Morphology](https://arxiv.org/abs/2511.06426).* arXiv:2511.06426 (2025).

```bibtex
@article{lau2025robust,
  author = {Lau, Kaikwan and Choi, Gary P. T.},
  title = {Robust Parametric Estimation of Avian Cranial Morphology},
  journal = {arXiv preprint arXiv:2511.06426},
  year = {2025},
  eprint = {2511.06426},
  archivePrefix = {arXiv},
  primaryClass = {q-bio.QM}
}
```

Code license: **[Apache License 2.0](LICENSE)**. Bundled MATLAB dependencies retain their [third-party licenses and credits](1_remeshing/Remeshing/THIRD_PARTY.md). See the original data sources for their attribution and reuse terms.

[Report an issue](https://github.com/kaikwanlau/skull-morphology/issues) · [Script reference](docs/REFERENCE.md)
