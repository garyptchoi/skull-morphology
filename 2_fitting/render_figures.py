#!/usr/bin/env python3
"""
render_figures.py — recreate the three-panel sphere-fit figures.

Reads the fitted sphere for each mesh out of measurement_sphere_fitting_ALL.xlsx
and redraws output/fit_sphere_batch/images/<stem>.png: 1800x650, left lateral / right lateral /
dorsal, translucent skull + blue wireframe sphere + red inlier points + green
centre.

Rows without exported orbital measurements (including Peromyscus controls)
are skipped. Their fit illustrations are produced by fit_sphere_batch.py.

Usage
-----
Set STL_DIR / XLSX / OUT_DIR below and press Run in PyCharm, or override
any of them from the command line:

    python render_figures.py stl_folder -x output/fit_sphere_batch/measurement_sphere_fitting_ALL.xlsx
    python render_figures.py stl_folder -f "C. flavaA.stl" --show
    python render_figures.py stl_folder -f "C. flavaA.stl" \
        --center -3.137 -3.039 1.731 --radius 2.703

Requires: numpy, pandas, openpyxl, pyvista (>=0.44).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pyvista as pv

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paths

HERE = Path(__file__).resolve().parent
STL_DIRS = [
    paths.CARDUELINES,
    paths.HONEYCREEPERS,
    paths.PEROMYSCUS,
]
BATCH_OUTPUT = HERE / "output" / "fit_sphere_batch"
XLSX_CANDIDATES = [
    BATCH_OUTPUT / "measurement_sphere_fitting_ALL.xlsx",
]
XLSX_SEARCH_ROOTS = [HERE / "output"]
OUT_DIR = BATCH_OUTPUT / "images"

WINDOW_SIZE = (1800, 650)
MESH_COLOR = "lightgray"
MESH_OPACITY = 0.45
SPHERE_COLOR = "blue"
SPHERE_RES = 40
POINT_COLOR = "red"
POINT_SIZE = 8.0
SEED_COLOR = "lime"
SEED_SIZE = 15.0
TITLE_FONT_SIZE = 10
LABEL_FONT_SIZE = 11
CAMERA_ZOOM = 1.0

VIEWS = [
    ("left lateral (from -y)", (0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
    ("right lateral (from +y)", (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    ("dorsal (from +z)", (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
]


def find_workbook() -> Path | None:
    for c in XLSX_CANDIDATES:
        if c.exists():
            return c

    skip = (".venv", "venv", "__pycache__", ".git", ".ipynb_checkpoints")
    hits = []
    for root in XLSX_SEARCH_ROOTS:
        if not root.is_dir():
            continue
        for hit in root.rglob("*sphere_fitting*.xls*"):
            if hit.name.startswith("~$"):
                continue
            if any(part in skip for part in hit.parts):
                continue
            hits.append(hit)

    if not hits:
        return None
    hits.sort(key=lambda h: (len(h.relative_to(h.anchor).parts),
                             -h.stat().st_mtime))
    return hits[0]


def find_mesh(name: str, dirs: list[Path]) -> Path | None:
    for d in dirs:
        hit = d / name
        if hit.exists():
            return hit
    target = name.lower()
    for d in dirs:
        for hit in d.rglob("*"):
            if hit.is_file() and hit.name.lower() == target:
                return hit
    return None


def inlier_points(mesh: pv.PolyData, center: np.ndarray, radius: float,
                  n_inliers: int | None, shell: float = 1.5) -> np.ndarray:
    verts = np.asarray(mesh.points, dtype=float)
    d = np.linalg.norm(verts - center, axis=1)
    near = d <= shell * radius
    idx = np.flatnonzero(near)
    if idx.size == 0:
        return np.empty((0, 3))
    resid = np.abs(d[idx] - radius)
    if n_inliers is None:
        return verts[idx[resid <= 0.15 * radius]]
    order = np.argsort(resid)[:int(n_inliers)]
    return verts[idx[order]]


def render(mesh: pv.PolyData, center, radius: float, points: np.ndarray,
           title: str = "", out_png: Path | None = None, show: bool = False,
           seed=None):
    center = np.asarray(center, dtype=float).reshape(3)
    focus = np.array(mesh.center)
    dist = float(np.ptp(np.array(mesh.bounds).reshape(3, 2), axis=1).max()) * 2.0

    pl = pv.Plotter(shape=(1, 3), window_size=WINDOW_SIZE,
                    off_screen=not show, border=False)
    pl.set_background("white")

    sphere = pv.Sphere(radius=radius, center=center,
                       theta_resolution=SPHERE_RES, phi_resolution=SPHERE_RES)

    for col, (label, direction, up) in enumerate(VIEWS):
        pl.subplot(0, col)
        pl.add_mesh(mesh, color=MESH_COLOR, opacity=MESH_OPACITY)
        pl.add_mesh(sphere, style="wireframe", color=SPHERE_COLOR, line_width=1)
        if len(points):
            pl.add_mesh(pv.PolyData(points), color=POINT_COLOR,
                        point_size=POINT_SIZE, render_points_as_spheres=True)
        if seed is not None:
            pl.add_mesh(pv.PolyData(np.asarray(seed).reshape(1, 3)),
                        color=SEED_COLOR, point_size=SEED_SIZE,
                        render_points_as_spheres=True)

        if col == 0 and title:
            pl.add_text(title, position="upper_left",
                        font_size=TITLE_FONT_SIZE, color="black")
        pl.add_text(label, position="lower_left",
                    font_size=LABEL_FONT_SIZE, color="black")

        pl.camera_position = [tuple(focus + np.array(direction) * dist),
                              tuple(focus), tuple(up)]
        pl.reset_camera()
        pl.camera.zoom(CAMERA_ZOOM)

    if show:
        pl.show()
    else:
        pl.screenshot(str(out_png))
        pl.close()


def title_for(row) -> str:
    parts = [str(row["filename"]), f"r = {row['sphere_radius']:.2f} mm"]
    if row.get("n_inliers") is not None:
        parts.append(f"{int(row['n_inliers'])} inliers")
    if row.get("seed_attempt") is not None:
        parts.append(f"seed attempt {int(row['seed_attempt'])}")
    if row.get("rms_over_radius") is not None:
        parts.append(f"RMS/r = {row['rms_over_radius']:.3f}")
    return "   ".join(parts)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("stl_dir", type=Path, nargs="*", default=STL_DIRS,
                   help="one or more folders holding the .stl meshes "
                        "(default: the STL_DIRS list at the top of this file)")
    p.add_argument("-x", "--xlsx", type=Path, default=None,
                   help="measurement_sphere_fitting_ALL.xlsx")
    p.add_argument("-o", "--out-dir", type=Path, default=OUT_DIR)
    p.add_argument("-f", "--filename", help="render only this mesh")
    p.add_argument("--show", action="store_true",
                   help="open a window instead of writing a PNG")
    p.add_argument("--center", type=float, nargs=3, metavar=("X", "Y", "Z"))
    p.add_argument("--radius", type=float)
    args = p.parse_args(argv)

    stl_dirs = [Path(d) for d in args.stl_dir]
    missing = [d for d in stl_dirs if not d.is_dir()]
    if missing:
        print("  !! these mesh folders do not exist and will be skipped:")
        for d in missing:
            print(f"     {d}")
    stl_dirs = [d for d in stl_dirs if d.is_dir()]
    if not stl_dirs:
        p.error(f"no mesh folders found\n"
                f"Edit STL_DIRS at the top of {Path(__file__).name}, "
                f"or pass the folders as arguments.")

    if args.xlsx is None and not (args.center and args.radius):
        args.xlsx = find_workbook()
        if args.xlsx is None:
            p.error("no sphere-fitting workbook found under:\n  "
                    + "\n  ".join(str(r) for r in XLSX_SEARCH_ROOTS)
                    + "\nRun fit_sphere_batch.py first (it writes output/fit_sphere_batch/), "
                      "or pass -x /path/to/measurement_sphere_fitting_ALL.xlsx")
        print(f"  workbook: {args.xlsx}")
    elif args.xlsx is not None and not args.xlsx.exists():
        p.error(f"workbook not found: {args.xlsx}")

    if args.xlsx:
        import pandas as pd
        df = pd.read_excel(args.xlsx)
        missing = [c for c in ("filename", "sphere_radius", "sphere_center_x",
                               "sphere_center_y", "sphere_center_z")
                   if c not in df.columns]
        if missing:
            p.error(f"{args.xlsx} is missing required column(s): "
                    f"{', '.join(missing)}")
        for opt in ("n_inliers", "seed_attempt", "rms_over_radius"):
            if opt not in df.columns:
                df[opt] = None
        print(f"  columns: {len(df.columns)}, rows: {len(df)}")
        rows = df.astype(object).where(df.notna(), None).to_dict("records")
        if args.filename:
            rows = [r for r in rows if r["filename"] == args.filename]
            if not rows:
                p.error(f"{args.filename} is not in the workbook")
    elif args.filename and args.center and args.radius:
        rows = [{"filename": args.filename, "sphere_radius": args.radius,
                 "sphere_center_x": args.center[0],
                 "sphere_center_y": args.center[1],
                 "sphere_center_z": args.center[2],
                 "n_inliers": None, "seed_attempt": None,
                 "rms_over_radius": None}]
    else:
        p.error("give --xlsx, or --filename with --center and --radius")

    if not args.show:
        args.out_dir.mkdir(parents=True, exist_ok=True)

    for row in rows:
        fit_values = [row["sphere_radius"], row["sphere_center_x"],
                      row["sphere_center_y"], row["sphere_center_z"]]
        if any(value is None for value in fit_values) or not np.isfinite(
                np.asarray(fit_values, dtype=float)).all():
            print(f"  {row['filename']}: skipped (no exported orbital measurements)")
            continue
        stl = find_mesh(row["filename"], stl_dirs)
        if stl is None:
            print(f"  !! {row['filename']} not found in any mesh folder")
            continue

        mesh = pv.read(stl).clean()
        center = np.array([row["sphere_center_x"],
                           row["sphere_center_y"],
                           row["sphere_center_z"]])
        pts = inlier_points(mesh, center, row["sphere_radius"], row.get("n_inliers"))

        out = None if args.show else args.out_dir / f"{stl.stem}.png"
        render(mesh, center, row["sphere_radius"], pts,
               title=title_for(row), out_png=out, show=args.show)
        print(f"  {row['filename']} -> {out if out else 'window'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
