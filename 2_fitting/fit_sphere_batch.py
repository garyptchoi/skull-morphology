
import os
import numpy as np
import pandas as pd
import pyvista as pv
import trimesh
from pathlib import Path
from scipy.optimize import minimize

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paths
from measurement_exports import export_measurements, is_rodent_filename, NO_ORBIT_REASON


HERE = Path(__file__).resolve().parent

DIRECTORY_PATHS = [
    paths.CARDUELINES,
    paths.HONEYCREEPERS,
    paths.PEROMYSCUS,
]

OUTPUT_DIR = paths.output_dir(__file__)
ENABLE_VISUALIZATION = True
SHOW_INTERACTIVE = False


CURVATURE_RADIUS = 2.0
TARGET_POINT_COUNT = 400
MIN_CONNECTED_POINTS = 20

MIN_ORBIT_RADIUS = 2.0
MAX_ORBIT_RADIUS = 6.0

ROI_START_PERCENT = 0.30
ROI_END_PERCENT = 0.70

MAX_SEED_ATTEMPTS = 15
ROBUST_FIT_OUTLIER_STD = 2.0

FOLDER_OVERRIDES = {
    "Peromyscus": {
        "MIN_ORBIT_RADIUS": 1.0,
        "MAX_ORBIT_RADIUS": 8.0,
        "CURVATURE_RADIUS": 1.5,
    },
}


def params_for(folder_name):
    p = {k: globals()[k] for k in
         ("CURVATURE_RADIUS", "TARGET_POINT_COUNT", "MIN_CONNECTED_POINTS",
          "MIN_ORBIT_RADIUS", "MAX_ORBIT_RADIUS", "ROI_START_PERCENT",
          "ROI_END_PERCENT", "MAX_SEED_ATTEMPTS", "ROBUST_FIT_OUTLIER_STD")}
    p.update(FOLDER_OVERRIDES.get(folder_name, {}))
    return p


WINDOW_SIZE = (1800, 650)
MESH_COLOR = "lightgrey"
MESH_OPACITY = 0.4
SPHERE_COLOR = "blue"
SPHERE_LINE_WIDTH = 2
POINT_COLOR = "crimson"
POINT_SIZE = 6
SEED_COLOR = "lime"
SEED_SIZE = 15
TITLE_FONT_SIZE = 10
LABEL_FONT_SIZE = 11

VIEWS = [
    ("left lateral (from -y)", (0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
    ("right lateral (from +y)", (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    ("dorsal (from +z)", (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
]

COLUMNS = [
    "filename", "length_x", "width_y", "height_z",
    "sphere_radius", "sphere_center_x", "sphere_center_y", "sphere_center_z",
    "curvature", "seed_attempt", "n_candidates", "n_inliers",
    "rms_residual_mm", "rms_over_radius", "fit_side", "rejected_attempts",
]



def sphere_loss_function(params, points):
    center = params[:3]
    radius = params[3]
    if radius <= 0:
        return 1e9
    distances = np.linalg.norm(points - center, axis=1)
    return np.sum((distances - radius) ** 2)


def fit_sphere_iteratively(points, max_iterations=3, outlier_std_dev=2.0):
    current_points = points.copy()
    result = None
    for _ in range(max_iterations):
        if len(current_points) < 4:
            return None, None, current_points

        initial_center = np.mean(current_points, axis=0)
        initial_radius = np.mean(np.linalg.norm(current_points - initial_center, axis=1))
        initial_guess = np.append(initial_center, initial_radius)

        result = minimize(
            sphere_loss_function, initial_guess, args=(current_points,),
            method="L-BFGS-B",
            bounds=[(None, None), (None, None), (None, None), (1e-6, None)],
        )

        fit_center, fit_radius = result.x[:3], result.x[3]
        errors = np.abs(np.linalg.norm(current_points - fit_center, axis=1) - fit_radius)
        inlier_mask = errors < (errors.mean() + outlier_std_dev * errors.std())

        if np.all(inlier_mask):
            break
        current_points = current_points[inlier_mask]

    final = minimize(
        sphere_loss_function, result.x, args=(current_points,),
        method="L-BFGS-B",
        bounds=[(None, None), (None, None), (None, None), (1e-6, None)],
    )
    return final.x[:3], final.x[3], current_points


def rms_residual(points, center, radius):
    resid = np.linalg.norm(points - center, axis=1) - radius
    return float(np.sqrt(np.mean(resid ** 2)))



def save_figure(mesh, fit_center, fit_radius, picked_points, seed_point,
                title, out_png):
    pv_mesh = pv.wrap(mesh)
    focus = np.array(pv_mesh.center)
    dist = float(np.ptp(np.array(pv_mesh.bounds).reshape(3, 2), axis=1).max()) * 2.0

    plotter = pv.Plotter(shape=(1, 3), window_size=WINDOW_SIZE,
                         off_screen=not SHOW_INTERACTIVE, border=False)
    plotter.set_background("white")
    sphere = pv.Sphere(radius=fit_radius, center=fit_center,
                       theta_resolution=40, phi_resolution=40)

    for col, (label, direction, up) in enumerate(VIEWS):
        plotter.subplot(0, col)
        plotter.add_mesh(pv_mesh, style="surface", opacity=MESH_OPACITY, color=MESH_COLOR)
        plotter.add_mesh(sphere, style="wireframe", color=SPHERE_COLOR,
                         line_width=SPHERE_LINE_WIDTH)
        plotter.add_points(picked_points, color=POINT_COLOR, point_size=POINT_SIZE,
                           render_points_as_spheres=True)
        plotter.add_points(np.asarray(seed_point).reshape(1, 3), color=SEED_COLOR,
                           point_size=SEED_SIZE, render_points_as_spheres=True)

        if col == 0:
            plotter.add_text(title, position="upper_left",
                             font_size=TITLE_FONT_SIZE, color="black")
        plotter.add_text(label, position="lower_left",
                         font_size=LABEL_FONT_SIZE, color="black")

        plotter.camera_position = [tuple(focus + np.array(direction) * dist),
                                   tuple(focus), tuple(up)]
        plotter.reset_camera()
    if SHOW_INTERACTIVE:
        plotter.show()
    else:
        plotter.screenshot(str(out_png))
        plotter.close()



def process_file(file_path, P):
    original_mesh = trimesh.load_mesh(file_path)

    components = original_mesh.split(only_watertight=False)
    if len(components) > 1:
        processed_mesh = sorted(components, key=lambda c: len(c.vertices), reverse=True)[0]
    else:
        processed_mesh = original_mesh
    processed_mesh.process(validate=True)

    box_extents = processed_mesh.bounding_box.extents
    verts = processed_mesh.vertices

    x_min = processed_mesh.bounds[0, 0]
    x_range = box_extents[0]
    roi_mask = np.logical_and(
        verts[:, 0] > x_min + x_range * P["ROI_START_PERCENT"],
        verts[:, 0] < x_min + x_range * P["ROI_END_PERCENT"],
    )
    if not np.any(roi_mask):
        roi_mask = np.ones(len(verts), dtype=bool)

    mean_curvatures = trimesh.curvature.discrete_mean_curvature_measure(
        processed_mesh, verts, radius=P["CURVATURE_RADIUS"]
    )
    curvatures_in_roi = mean_curvatures.copy()
    curvatures_in_roi[~roi_mask] = 1.0

    top_N_seed_indices = np.argsort(curvatures_in_roi)[:P["MAX_SEED_ATTEMPTS"]]
    if curvatures_in_roi[top_N_seed_indices[0]] == 1.0:
        return None, ["no concave points in ROI"], None

    initial_mask = np.zeros(len(verts), dtype=bool)
    initial_mask[np.argsort(mean_curvatures)[:P["TARGET_POINT_COUNT"]]] = True
    valid_indices_mask = np.logical_and(initial_mask, roi_mask)

    valid_edges_mask = valid_indices_mask[processed_mesh.edges].all(axis=1)
    selected_edges = processed_mesh.edges[valid_edges_mask]
    components = trimesh.graph.connected_components(selected_edges) if len(selected_edges) else []

    tags = []
    for attempt, seed_index in enumerate(top_N_seed_indices, start=1):
        if not valid_indices_mask[seed_index]:
            tags.append(f"a{attempt}:skip")
            continue

        final_indices = np.array([], dtype=int)
        for component in components:
            if seed_index in component:
                final_indices = np.array(component)
                break
        if len(final_indices) == 0 and components:
            final_indices = np.array(max(components, key=len))

        n_candidates = len(final_indices)
        if n_candidates < P["MIN_CONNECTED_POINTS"]:
            tags.append(f"a{attempt}:{n_candidates}pts")
            continue

        picked_points = verts[final_indices]
        fit_center, fit_radius, inliers = fit_sphere_iteratively(
            picked_points, outlier_std_dev=P["ROBUST_FIT_OUTLIER_STD"]
        )
        if fit_center is None:
            tags.append(f"a{attempt}:fitfail")
            continue

        if not (P["MIN_ORBIT_RADIUS"] < fit_radius < P["MAX_ORBIT_RADIUS"]):
            tags.append(f"a{attempt}:r={fit_radius:.2f}")
            continue

        rms = rms_residual(inliers, fit_center, fit_radius)
        row = {
            "filename": os.path.basename(file_path),
            "length_x": box_extents[0],
            "width_y": box_extents[1],
            "height_z": box_extents[2],
            "sphere_radius": fit_radius,
            "sphere_center_x": fit_center[0],
            "sphere_center_y": fit_center[1],
            "sphere_center_z": fit_center[2],
            "curvature": 1 / fit_radius,
            "seed_attempt": attempt,
            "n_candidates": n_candidates,
            "n_inliers": len(inliers),
            "rms_residual_mm": rms,
            "rms_over_radius": rms / fit_radius,
            "fit_side": "y>0" if fit_center[1] > 0 else "y<0",
            "rejected_attempts": "; ".join(tags),
        }
        render_args = (processed_mesh, fit_center, fit_radius, inliers,
                       verts[seed_index])
        return row, tags, render_args

    return None, tags, None


def style_header(path):
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Border, Font, Side

    thin = Side(style="thin")
    wb = load_workbook(path)
    for cell in wb.active[1]:
        cell.font = Font(bold=True)
        cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)
        cell.alignment = Alignment(horizontal="center", vertical="top")
    wb.save(path)



if __name__ == "__main__":
    stl_files = []
    for d in DIRECTORY_PATHS:
        d = Path(d)
        if not d.is_dir():
            print(f"  !! folder not found, skipping: {d}")
            continue
        found = sorted(d.glob("*.stl")) + sorted(d.glob("*.STL"))
        print(f"  {d.name}: {len(found)} mesh(es)")
        stl_files.extend(found)

    if not stl_files:
        raise SystemExit(f"Error: no .stl files found in {DIRECTORY_PATHS}")
    print(f"Found {len(stl_files)} STL files to process.\n")

    images_dir = OUTPUT_DIR / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    results_list, failed_files_list = [], []
    per_folder = {}

    for i, file_path in enumerate(stl_files, start=1):
        name = os.path.basename(file_path)
        print(f"--- {i}/{len(stl_files)}: {name} ---")

        P = params_for(file_path.parent.name)
        try:
            row, tags, render_args = process_file(str(file_path), P)
        except Exception as e:
            print(f"  -> error, skipping: {e}")
            failed_files_list.append((name, f"error: {e}"))
            continue

        if row is None:
            print(f"  -> all {P['MAX_SEED_ATTEMPTS']} seed attempts failed.")
            failed_files_list.append((name, "; ".join(tags)))
            per_folder.setdefault(file_path.parent.name, [0, 0])[1] += 1
            continue

        results_list.append(row)
        per_folder.setdefault(file_path.parent.name, [0, 0])[0] += 1
        print(f"  -> r = {row['sphere_radius']:.4f} mm on attempt {row['seed_attempt']} "
              f"({row['n_inliers']}/{row['n_candidates']} inliers, "
              f"RMS/r = {row['rms_over_radius']:.3f})")

        if ENABLE_VISUALIZATION:
            mesh, fit_center, fit_radius, inliers, seed_point = render_args
            title = (f"{name}   r = {fit_radius:.2f} mm   {len(inliers)} inliers   "
                     f"seed attempt {row['seed_attempt']}   "
                     f"RMS/r = {row['rms_over_radius']:.3f}")
            save_figure(mesh, fit_center, fit_radius, inliers, seed_point,
                        title, images_dir / f"{Path(name).stem}.png")

    print("\n--- BATCH COMPLETE ---")
    print(f"--- {len(results_list)} / {len(stl_files)} files fitted. ---")
    for folder, (ok, bad) in per_folder.items():
        note = "  <-- check FOLDER_OVERRIDES" if ok == 0 else ""
        print(f"      {folder}: {ok} fitted, {bad} failed{note}")

    if results_list:
        xlsx = OUTPUT_DIR / "measurement_sphere_fitting_ALL.xlsx"
        export_measurements(pd.DataFrame(results_list, columns=COLUMNS)).to_excel(
            xlsx, index=False, engine="openpyxl")
        style_header(xlsx)
        print(f"Saved {xlsx}")

    with open(OUTPUT_DIR / "failed_files.txt", "w") as fh:
        for name, detail in failed_files_list:
            if is_rodent_filename(name):
                detail = NO_ORBIT_REASON
            fh.write(f"{name}\t{detail}\n")
    if failed_files_list:
        print(f"{len(failed_files_list)} failures logged to "
              f"{OUTPUT_DIR / 'failed_files.txt'}")
