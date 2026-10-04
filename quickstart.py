#!/usr/bin/env python3
"""Fit one prepared skull with the existing orbit fitter and export inspectable results.

Run from any working directory. No data files or original fitting code are modified.
This entry point measures one orbit; use 2_fitting/ for the full study workflow.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SETTINGS = dict(ROI_START_PERCENT=0.30, ROI_END_PERCENT=0.70,
                MIN_ORBIT_RADIUS=2.0, MAX_ORBIT_RADIUS=6.0,
                CURVATURE_RADIUS=2.0, TARGET_POINT_COUNT=400,
                MAX_SEED_ATTEMPTS=15, MIN_COMPONENT=20)


def load_fitter():
    spec = importlib.util.spec_from_file_location(
        "skull_orbit_reference", ROOT / "4_two_orbits" / "verify_fit.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run


def draw_inspection(mesh_path, fit, destination, diagnostic=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import trimesh
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    mesh = trimesh.load_mesh(mesh_path)
    components = mesh.split(only_watertight=False)
    if len(components) > 1:
        mesh = max(components, key=lambda component: len(component.vertices))
    mesh.process(validate=True)
    center = np.array([fit["cx"], fit["cy"], fit["cz"]])
    radius = fit["sphere_radius"]
    u, v = np.meshgrid(np.linspace(0, 2*np.pi, 30), np.linspace(0, np.pi, 18))
    sphere = (center[0] + radius*np.cos(u)*np.sin(v),
              center[1] + radius*np.sin(u)*np.sin(v),
              center[2] + radius*np.cos(v))
    fig = plt.figure(figsize=(14, 5), facecolor="#faf9f6")
    fit_label = "diagnostic sphere fit" if diagnostic else "orbital fit"
    fig.suptitle(f'{mesh_path.name}  |  {fit_label}', fontsize=17, x=0.035, ha="left")
    views = [(0, -90, "Lateral: from −y"), (0, 90, "Lateral: from +y"),
             (90, -90, "Dorsal: from +z")]
    bounds = mesh.bounds
    middle = bounds.mean(axis=0)
    half = max(mesh.extents) * 0.55
    for i, (elev, azim, title) in enumerate(views, 1):
        ax = fig.add_subplot(1, 3, i, projection="3d", facecolor="#faf9f6")
        light = np.array([0.3, -0.6, 0.75]); light /= np.linalg.norm(light)
        shade = 0.58 + 0.42 * np.clip(mesh.face_normals @ light, 0, 1)
        colors = shade[:, None] * np.array([0.73, 0.72, 0.68])[None, :]
        ax.add_collection3d(Poly3DCollection(mesh.triangles, facecolors=colors,
                                           edgecolor="none", alpha=0.30))
        ax.plot_wireframe(*sphere, color="#2547bf", linewidth=0.45, alpha=0.75)
        ax.scatter(*fit["_inliers"].T, color="#b54830", s=4, depthshade=False)
        for setter, c in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), middle):
            setter(c-half, c+half)
        ax.set_box_aspect((1, 1, 1), zoom=1.55)
        ax.set_proj_type("ortho")
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(title, fontsize=11)
    if diagnostic:
        info = "Peromyscus control: the fitted sphere does not identify the orbit."
        caption = "Blue: diagnostic fitted sphere. Red: retained points. No orbital measurements are reported."
    else:
        info = (f'Radius {radius:.4f} mm   ·   Curvature {fit["curvature"]:.4f} mm⁻¹'
                f'   ·   {fit["n_inliers"]} inliers   ·   RMS/radius {fit["fit_err_pct"]:.2f}%')
        caption = "Blue: fitted sphere. Red: retained points. Inspect anatomical placement before using the measurement."
    fig.text(0.035, 0.08, info, fontsize=11)
    fig.text(0.035, 0.025, caption, fontsize=9, color="#555555")
    fig.subplots_adjust(top=0.83, bottom=0.18, left=0.015, right=0.99, wspace=0.02)
    fig.savefig(destination, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mesh", type=Path,
                        default=ROOT / "data/DF_and_their_relatives/G.DifficilisA.stl",
                        help="One prepared, anatomically oriented STL in mm; finch settings are used.")
    parser.add_argument("--output", type=Path, default=ROOT / "output/quickstart",
                        help="Results directory, outside data/. Existing result files here are replaced.")
    args = parser.parse_args()
    mesh_path = args.mesh.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not mesh_path.is_file() or mesh_path.suffix.lower() != ".stl":
        parser.error(f"STL file not found: {mesh_path}")
    if output == ROOT / "data" or (ROOT / "data") in output.parents:
        parser.error("Choose an output directory outside the supplied data/ folder.")
    if output.exists() and not output.is_dir():
        parser.error("--output must be a directory.")
    try:
        import pandas as pd
        from measurement_exports import export_measurements, is_rodent_filename
        run = load_fitter()
    except ModuleNotFoundError as exc:
        parser.exit(2, f"Missing package: {exc.name}. Run: python -m pip install -r requirements-quickstart.txt\n")
    print(f"Fitting one prepared skull: {mesh_path.name}", flush=True)
    print("Using the supplied finch settings; input orientation and units are assumed.", flush=True)
    try:
        fit = run(str(mesh_path), **SETTINGS)
    except Exception as exc:
        parser.exit(1, f"Fitting failed ({type(exc).__name__}): {exc}\n")
    result = {key: value for key, value in fit.items() if not key.startswith("_")}
    result["s4_screen_pass"] = (bool(fit["n_inliers"] >= 40 and fit["fit_err_pct"] <= 10)
                                if fit["status"] == "ok" else None)
    table = export_measurements(pd.DataFrame([result]))
    result = table.astype(object).where(table.notna(), None).iloc[0].to_dict()
    diagnostic = is_rodent_filename(mesh_path.name)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "measurements.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(result))
        writer.writeheader()
        writer.writerow(result)
    versions = {}
    for name in ("numpy", "scipy", "pandas", "trimesh", "rtree", "networkx", "matplotlib"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not installed"
    record = dict(mesh=mesh_path.name, mesh_sha256=hashlib.sha256(mesh_path.read_bytes()).hexdigest(),
                  mesh_units="mm (assumed, not inferred from STL)", settings=SETTINGS,
                  python=platform.python_version(), packages=versions,
                  implementation="4_two_orbits/verify_fit.py:run", result=result,
                  interpretation=("Diagnostic sphere fit only; no orbital measurements are reported for Peromyscus."
                                  if diagnostic else
                                  "Numerical success and the S4 screen do not replace visual anatomical inspection."))
    (output / "run.json").write_text(json.dumps(record, indent=2, default=float, allow_nan=False) + "\n", encoding="utf-8")
    picture = output / "inspection.png"
    if fit["status"] != "ok":
        picture.unlink(missing_ok=True)
        print(f'No numerical fit: {fit["status"]}. Diagnostics saved to {output}')
        return 1
    try:
        draw_inspection(mesh_path, fit, picture, diagnostic=diagnostic)
    except Exception as exc:
        picture.unlink(missing_ok=True)
        saved = "Diagnostics" if diagnostic else "Measurements"
        print(f"{saved} saved, but the inspection image could not be rendered: {exc}")
        return 1
    if diagnostic:
        print("Diagnostic sphere fit completed; no orbital measurements are reported.")
        print(f"Results: {output}\nOpen inspection.png to inspect the diagnostic fit placement.")
    else:
        print(f'Radius: {fit["sphere_radius"]:.4f} mm; curvature: {fit["curvature"]:.4f} mm^-1')
        print(f'Inliers: {fit["n_inliers"]}; RMS/radius: {fit["fit_err_pct"]:.2f}%')
        print(f"Results: {output}\nOpen inspection.png and check that the sphere is in the orbit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
