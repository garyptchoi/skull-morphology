import sys, os, glob
import numpy as np
import trimesh
from scipy.optimize import minimize
import pandas as pd


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
    for i in range(max_iterations):
        if len(current_points) < 4:
            return None, None, current_points
        initial_center = np.mean(current_points, axis=0)
        initial_radius = np.mean(np.linalg.norm(current_points - initial_center, axis=1))
        initial_guess = np.append(initial_center, initial_radius)
        result = minimize(sphere_loss_function, initial_guess, args=(current_points,),
                          method='L-BFGS-B',
                          bounds=[(None, None), (None, None), (None, None), (1e-6, None)])
        fit_center, fit_radius = result.x[:3], result.x[3]
        distances_to_center = np.linalg.norm(current_points - fit_center, axis=1)
        errors = np.abs(distances_to_center - fit_radius)
        mean_error, std_error = np.mean(errors), np.std(errors)
        inlier_mask = errors < (mean_error + outlier_std_dev * std_error)
        if np.all(inlier_mask):
            break
        current_points = current_points[inlier_mask]
    final_result = minimize(sphere_loss_function, result.x, args=(current_points,), method='L-BFGS-B',
                            bounds=[(None, None), (None, None), (None, None), (1e-6, None)])
    return final_result.x[:3], final_result.x[3], current_points


def run(file_path, ROI_START_PERCENT=0.30, ROI_END_PERCENT=0.70, MIN_ORBIT_RADIUS=2.0, MAX_ORBIT_RADIUS=6.0,
        CURVATURE_RADIUS=2.0, TARGET_POINT_COUNT=400, MAX_SEED_ATTEMPTS=15, MIN_COMPONENT=20,
        record_unclipped=False, half=None):
    original_mesh = trimesh.load_mesh(file_path)
    components = original_mesh.split(only_watertight=False)
    if len(components) > 1:
        processed_mesh = sorted(components, key=lambda c: len(c.vertices), reverse=True)[0]
    else:
        processed_mesh = original_mesh
    processed_mesh.process(validate=True)
    box_extents = processed_mesh.bounding_box.extents
    bounds = processed_mesh.bounds
    x_min = bounds[0, 0]
    x_range = box_extents[0]
    roi_x_min_threshold = x_min + (x_range * ROI_START_PERCENT)
    roi_x_max_threshold = x_min + (x_range * ROI_END_PERCENT)
    roi_mask = np.logical_and(processed_mesh.vertices[:, 0] > roi_x_min_threshold,
                              processed_mesh.vertices[:, 0] < roi_x_max_threshold)
    if half == 'y<0':
        roi_mask = np.logical_and(roi_mask, processed_mesh.vertices[:, 1] < 0)
    elif half == 'y>0':
        roi_mask = np.logical_and(roi_mask, processed_mesh.vertices[:, 1] > 0)
    if not np.any(roi_mask):
        roi_mask = np.ones(len(processed_mesh.vertices), dtype=bool)

    mean_curvatures = trimesh.curvature.discrete_mean_curvature_measure(
        processed_mesh, processed_mesh.vertices, radius=CURVATURE_RADIUS)
    curvatures_in_roi = mean_curvatures.copy()
    curvatures_in_roi[~roi_mask] = 1.0
    sorted_curvature_indices_local = np.argsort(curvatures_in_roi)
    top_N_seed_indices = np.arange(len(processed_mesh.vertices))[sorted_curvature_indices_local[:MAX_SEED_ATTEMPTS]]
    if curvatures_in_roi[top_N_seed_indices[0]] == 1.0:
        return dict(filename=os.path.basename(file_path), status='no_concave')

    sorted_indices = np.argsort(mean_curvatures)
    initial_mask = np.zeros(len(processed_mesh.vertices), dtype=bool)
    initial_mask[sorted_indices[:TARGET_POINT_COUNT]] = True
    valid_indices_mask = np.logical_and(initial_mask, roi_mask)

    rejected = []
    for attempt, seed_index in enumerate(top_N_seed_indices):
        if not valid_indices_mask[seed_index]:
            rejected.append((attempt + 1, 'seed_not_valid'))
            continue
        final_indices = np.array([])
        valid_edges_mask = valid_indices_mask[processed_mesh.edges].all(axis=1)
        selected_edges = processed_mesh.edges[valid_edges_mask]
        if len(selected_edges) > 0:
            comps = trimesh.graph.connected_components(selected_edges)
            if comps:
                for component in comps:
                    if seed_index in component:
                        final_indices = np.array(component)
                        break
                if len(final_indices) == 0:
                    final_indices = np.array(max(comps, key=len))
        if len(final_indices) < MIN_COMPONENT:
            rejected.append((attempt + 1, f'small_component_{len(final_indices)}'))
            continue
        picked_points = processed_mesh.vertices[final_indices]
        n_candidates = len(picked_points)
        fit_center, fit_radius, final_points = fit_sphere_iteratively(picked_points, outlier_std_dev=2.0)
        if fit_center is None:
            rejected.append((attempt + 1, 'fit_failed'))
            continue
        if not (MIN_ORBIT_RADIUS < fit_radius < MAX_ORBIT_RADIUS):
            rejected.append((attempt + 1, f'radius_{fit_radius:.2f}'))
            continue
        residuals = np.abs(np.linalg.norm(final_points - fit_center, axis=1) - fit_radius)
        rms = float(np.sqrt(np.mean(residuals ** 2)))
        out = dict(filename=os.path.basename(file_path), status='ok',
                   length_x=box_extents[0], width_y=box_extents[1], height_z=box_extents[2],
                   sphere_radius=fit_radius, cx=fit_center[0], cy=fit_center[1], cz=fit_center[2],
                   curvature=1 / fit_radius, seed_attempt=attempt + 1, n_candidates=n_candidates,
                   n_inliers=len(final_points), rms_mm=rms, fit_err_pct=100 * rms / fit_radius,
                   fit_side='y<0' if fit_center[1] < 0 else 'y>0',
                   centre_frac=(fit_center[0] - x_min) / x_range,
                   n_vertices=len(processed_mesh.vertices),
                   rejected=';'.join(f'{a}:{r}' for a, r in rejected))
        out['_inliers'] = final_points; out['_seed'] = processed_mesh.vertices[seed_index]
        if record_unclipped:
            valid_full = initial_mask.copy()
            ve = valid_full[processed_mesh.edges].all(axis=1)
            se = processed_mesh.edges[ve]
            comps = trimesh.graph.connected_components(se)
            n_full = 0
            for component in comps:
                if seed_index in component:
                    n_full = len(component)
                    break
            out['n_candidates_unclipped'] = n_full
        return out
    return dict(filename=os.path.basename(file_path), status='all_seeds_failed',
                length_x=box_extents[0], width_y=box_extents[1], height_z=box_extents[2],
                rejected=';'.join(f'{a}:{r}' for a, r in rejected))


if __name__ == '__main__':
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import paths
    from measurement_exports import export_measurements
    args = sys.argv[1:]
    if args and args[-1].lower().endswith('.csv'):
        folders, out_csv = args[:-1], args[-1]
    else:
        folders, out_csv = args, str(paths.output_dir(__file__) / 'verify_fit_results.csv')
    if not folders:
        folders = [str(paths.FINCHES), str(paths.HONEYCREEPERS), str(paths.CARDUELINES), str(paths.PEROMYSCUS)]
    rows = []
    for folder in folders:
        stl_files = sorted(glob.glob(os.path.join(folder, '*.stl')))
        if not stl_files:
            print(f'No .stl file found in {folder}', flush=True)
        for fp in stl_files:
            r = run(fp, record_unclipped=True)
            r['folder'] = os.path.basename(folder.rstrip('/'))
            rows.append(r)
            print(r.get('filename'), r.get('status'), r.get('sphere_radius'), r.get('n_inliers'), r.get('fit_err_pct'), flush=True)
    table = pd.DataFrame(rows)
    table = table.drop(columns=[c for c in table.columns if c.startswith('_')])
    export_measurements(table).to_csv(out_csv, index=False)
    n_ok = int((table['status'] == 'ok').sum()) if 'status' in table else 0
    print(f'\n{len(table)} skulls ({n_ok} fitted); results written to {out_csv}')
