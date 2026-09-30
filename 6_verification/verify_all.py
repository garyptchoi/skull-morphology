
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paths

QUICK_RUN = False
PRINT_TABLES = False
OTHER_TAXA = True
SHOW_FITS = False
USE_TESTED_VERSIONS = False
OPEN_RESULTS = False
REPOSITORY_FOLDER = str(paths.DATA)

import html
import importlib
import importlib.metadata
import importlib.util
import os
import platform
import re
import subprocess
import sys
import textwrap
import time
import unicodedata
import webbrowser
from datetime import datetime
from pathlib import Path

TESTED_VERSIONS = {'numpy': '2.2.6', 'scipy': '1.13.1', 'pandas': '2.3.3', 'openpyxl': '3.1.5',
                   'statsmodels': '0.14.5', 'trimesh': '4.8.3', 'rtree': '1.4.1', 'networkx': '3.6'}
SCRIPT = os.path.basename(os.path.abspath(__file__))
MEASURED_MESHES = 100


def installed_version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def install_packages():
    wanted = dict(TESTED_VERSIONS, **({'pyvista': None} if SHOW_FITS else {}))
    if USE_TESTED_VERSIONS:
        todo = [f'{name}=={version}' for name, version in wanted.items() if version and installed_version(name) != version]
        todo += [name for name, version in wanted.items() if not version and importlib.util.find_spec(name) is None]
    else:
        todo = [name for name in wanted if importlib.util.find_spec(name) is None]
    if not todo:
        return
    print('Installing into the Python interpreter of this project: ' + ', '.join(todo), flush=True)
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *todo])
    except (subprocess.CalledProcessError, OSError):
        sys.exit('Automatic installation failed. In PyCharm, open Settings > Project > Python Interpreter, click +, '
                 'install ' + ', '.join(todo) + ', and click Run again.')
    importlib.invalidate_caches()


install_packages()

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from measurement_exports import export_measurements  # noqa: E402
import scipy  # noqa: E402
import statsmodels  # noqa: E402
import statsmodels.api as sm  # noqa: E402
import trimesh  # noqa: E402
from scipy import stats  # noqa: E402
from scipy.optimize import minimize  # noqa: E402




DIMS = ['length_x', 'width_y', 'height_z']
MODEL_COEFFICIENTS = np.array([0.5653, -0.0013, -0.0004, -0.0153])
DF, REL = "Darwin's finches", 'Relatives'
GENERA = ['Camarhynchus', 'Certhidea', 'Geospiza', 'Pinaroloxias', 'Platyspiza',
          'Coereba', 'Euneornis', 'Loxigilla', 'Loxipasser', 'Melopyrrha', 'Tiaris']
WIDE_SPECIES = ['magnirostris', 'violacea', 'portoricensis']


SPECIES = [
    ('C.Pallidus', DF, 'Camarhynchus', 'pallidus', [40, 60, 60, 60]),
    ('C.Parvulus', DF, 'Camarhynchus', 'parvulus', [60, 50, 58, 58, 58]),
    ('C.Psittacula', DF, 'Camarhynchus', 'psittacula', [59, 60, 55, 60]),
    ('C2.Fusca', DF, 'Certhidea', 'fusca', [30, 62]),
    ('C2.Olivacea', DF, 'Certhidea', 'olivacea', [62, 68, 60]),
    ('G.Conirostris', DF, 'Geospiza', 'conirostris', [60, 60, 60, 62, 62, 60, 60]),
    ('G.Difficilis', DF, 'Geospiza', 'difficilis', [62, 30]),
    ('G.Fortis', DF, 'Geospiza', 'fortis', [60, 60, 50, 60, 60]),
    ('G.Fuliginosa', DF, 'Geospiza', 'fuliginosa', [50, 60, 60, 60, 61, 60]),
    ('G.Magnirostris', DF, 'Geospiza', 'magnirostris', [60, 60, 61, 60, 60]),
    ('G.Scandens', DF, 'Geospiza', 'scandens', [60, 62]),
    ('G.Septentrionalist', DF, 'Geospiza', 'septentrionalis', [60, 62]),
    ('P.Crassirostris', DF, 'Platyspiza', 'crassirostris', [60, 60, 60, 60]),
    ('P2.Inornata', DF, 'Pinaroloxias', 'inornata', [60, 61]),
    ('C.flaveola', REL, 'Coereba', 'flaveola', [55, 55, 55, 40, 60]),
    ('E.campestris', REL, 'Euneornis', 'campestris', [62, 60, 62, 60, 62]),
    ('L.anoxanthus', REL, 'Loxipasser', 'anoxanthus', [60, 60, 60, 35, 65]),
    ('L.noctis', REL, 'Loxigilla', 'noctis', [60, 50, 60, 60]),
    ('L.portoricensis', REL, 'Loxigilla', 'portoricensis', [50, 60, 60, 60, 60]),
    ('L.violacea', REL, 'Loxigilla', 'violacea', [60, 60, 60, 60, 55]),
    ('M.nigra', REL, 'Melopyrrha', 'nigra', [60, 60, 48, 60]),
    ('T.Bicolor', REL, 'Tiaris', 'bicolor', [60, 60, 62, 60, 60]),
    ('T.canora', REL, 'Tiaris', 'canora', [60, 60, 58, 59, 59]),
    ('T.olivacea', REL, 'Tiaris', 'olivaceus', [60, 59, 75, 60]),
]


def specimen_table(source):
    where = f'in {source}' if isinstance(source, str) else 'in Dataset.xlsx'
    files = sorted(name for name in (os.listdir(source) if isinstance(source, str) else map(str, source))
                   if name.endswith('.stl'))
    rows = []
    for prefix, group, genus, species, remeshing in SPECIES:
        matching = [name for name in files if re.fullmatch(re.escape(prefix) + r'[A-Z]\.stl', name)]
        if len(matching) != len(remeshing):
            sys.exit(f'Expected {len(remeshing)} mesh files starting with {prefix} {where}, found {len(matching)}.')
        for name, value in zip(matching, remeshing):
            rows.append(dict(specimen_id=len(rows) + 1, filename=name, group=group, genus=genus, species=species,
                             remeshing_parameter=value))
    return pd.DataFrame(rows)


def load_skull(path, align_full_mesh=False):
    raw = trimesh.load_mesh(path)
    parts = raw.split(only_watertight=False)
    mesh = sorted(parts, key=lambda part: len(part.vertices), reverse=True)[0]
    topology = dict(closed=bool(raw.is_watertight), n_components=len(parts),
                    genus_largest=int(round(1 - mesh.euler_number / 2)))
    if align_full_mesh:
        # Alignment uses all input vertices; fragment removal belongs to fitting.
        # Preserve the topology of the original mesh in the returned metadata.
        oriented = align_by_principal_axes(raw)
        mesh = max(oriented.split(only_watertight=False), key=lambda part: len(part.vertices))
    mesh.process(validate=True)
    return mesh, topology


def skull_dimensions(mesh):
    length, width, height = mesh.bounding_box.extents
    return dict(length_x=float(length), width_y=float(width), height_z=float(height))


ORBIT_SETTINGS = dict(
    curvature_radius=2.0,
    candidate_count=400,
    band_start=0.30,
    band_end=0.70,
    max_seeds=15,
    min_patch=20,
    min_radius=2.0,
    max_radius=6.0,
    outlier_std=2.0,
    max_iterations=3,
    min_points=4,
    tolerance=1e-5,
)


def sphere_loss_function(params, points):
    center = params[:3]
    radius = params[3]
    if radius <= 0:
        return 1e9
    distances = np.linalg.norm(points - center, axis=1)
    return np.sum((distances - radius) ** 2)


def fit_sphere_iteratively(points, max_iterations=3, outlier_std_dev=2.0, min_points=4, gtol=1e-5):
    current_points = points.copy()
    for i in range(max_iterations):
        if len(current_points) < min_points:
            return None, None, current_points

        initial_center = np.mean(current_points, axis=0)
        initial_radius = np.mean(np.linalg.norm(current_points - initial_center, axis=1))
        initial_guess = np.append(initial_center, initial_radius)

        result = minimize(
            sphere_loss_function,
            initial_guess,
            args=(current_points,),
            method='L-BFGS-B',
            bounds=[(None, None), (None, None), (None, None), (1e-6, None)],
            options={'gtol': gtol}
        )

        fit_center, fit_radius = result.x[:3], result.x[3]

        distances_to_center = np.linalg.norm(current_points - fit_center, axis=1)
        errors = np.abs(distances_to_center - fit_radius)
        mean_error, std_error = np.mean(errors), np.std(errors)

        inlier_mask = errors < (mean_error + outlier_std_dev * std_error)

        if np.all(inlier_mask):
            break

        current_points = current_points[inlier_mask]

    final_result = minimize(sphere_loss_function, result.x, args=(current_points,), method='L-BFGS-B',
                            bounds=[(None, None), (None, None), (None, None), (1e-6, None)], options={'gtol': gtol})
    return final_result.x[:3], final_result.x[3], current_points


def fit_orbit(mesh, side=None, **settings):
    s = {**ORBIT_SETTINGS, **settings}
    v = mesh.vertices
    x_min, x_range = mesh.bounds[0, 0], mesh.bounding_box.extents[0]
    band = (v[:, 0] > x_min + x_range * s['band_start']) & (v[:, 0] < x_min + x_range * s['band_end'])
    if not band.any():
        band[:] = True
    if side is not None:
        band = band & ((v[:, 1] >= 0) if side == 'right' else (v[:, 1] < 0))
        if not band.any():
            return None
    curvature = trimesh.curvature.discrete_mean_curvature_measure(mesh, v, radius=s['curvature_radius'])
    in_band = curvature.copy()
    in_band[~band] = 1.0
    seeds = np.argsort(in_band)[:s['max_seeds']]
    if in_band[seeds[0]] == 1.0:
        return None
    candidate = np.zeros(len(v), dtype=bool)
    candidate[np.argsort(curvature)[:s['candidate_count']]] = True
    candidate &= band
    edges = mesh.edges[candidate[mesh.edges].all(axis=1)]
    components = trimesh.graph.connected_components(edges) if len(edges) else []
    rejected = []
    for rank, seed in enumerate(seeds, start=1):
        if not candidate[seed] or not len(components):
            continue
        patch = next((np.asarray(c) for c in components if seed in c), None)
        if patch is None:
            patch = np.asarray(max(components, key=len))
        if len(patch) < s['min_patch']:
            continue
        center, radius, inliers = fit_sphere_iteratively(v[patch], max_iterations=s['max_iterations'],
                                                         outlier_std_dev=s['outlier_std'], min_points=s['min_points'],
                                                         gtol=s['tolerance'])
        if center is None:
            continue
        if not (s['min_radius'] < radius < s['max_radius']):
            rejected.append(float(radius))
            continue
        return dict(sphere_radius=float(radius), center=center, inliers=inliers, patch_size=len(patch),
                    seed_point=v[seed], seed_rank=rank, rejected_radii=rejected)
    return None


BRAINCASE_SETTINGS = dict(
    axis='x',
    rear_fraction=0.40,
    curvature_radius=3.0,
    candidate_count=1200,
    min_patch=30,
    max_seed_to_centre=80.0,
    outlier_std=1.5,
    max_iterations=3,
    min_points=6,
    tolerance=1e-5,
)


def axis_aligned_ellipsoid_loss_function(params, points):
    center = params[:3]
    axes_lengths = params[3:6]

    if any(a <= 1e-6 for a in axes_lengths):
        return 1e9

    points_transformed = points - center
    distances = np.sum((points_transformed / axes_lengths) ** 2, axis=1)
    return np.sum((distances - 1.0) ** 2)


def fit_axis_aligned_ellipsoid_iteratively(points, max_iterations=3, outlier_std_dev=1.5, min_points=6, gtol=1e-5):
    current_points = points.copy()
    last_successful_result = None

    for i in range(max_iterations):
        if len(current_points) < min_points:
            return None, None

        center_guess = np.mean(current_points, axis=0)
        centered_points = current_points - center_guess
        axes_guess = np.std(centered_points, axis=0) * 2.0
        axes_guess[axes_guess < 1e-6] = 1e-6
        initial_guess = np.concatenate([center_guess, axes_guess])

        min_b = np.min(current_points, axis=0)
        max_b = np.max(current_points, axis=0)
        buffer = (max_b - min_b) * 0.5
        center_bounds = list(zip(min_b - buffer, max_b + buffer))
        axes_bounds = [(1e-6, None)] * 3
        optimizer_bounds = center_bounds + axes_bounds

        result = minimize(
            axis_aligned_ellipsoid_loss_function,
            initial_guess,
            args=(current_points,),
            method='L-BFGS-B',
            bounds=optimizer_bounds,
            options={'gtol': gtol}
        )

        if result.success:
            last_successful_result = result

        fit_params = result.x
        fit_center = fit_params[:3]
        fit_axes = fit_params[3:6]

        points_transformed = current_points - fit_center
        distances = np.sum((points_transformed / fit_axes) ** 2, axis=1)
        errors = np.abs(distances - 1.0)
        mean_error, std_error = np.mean(errors), np.std(errors)

        if std_error < 1e-6: break
        inlier_mask = errors < (mean_error + outlier_std_dev * std_error)
        if np.all(inlier_mask): break
        current_points = current_points[inlier_mask]

    if last_successful_result is None:
        return None, None

    final_result = minimize(
        axis_aligned_ellipsoid_loss_function,
        last_successful_result.x,
        args=(current_points,),
        method='L-BFGS-B',
        bounds=optimizer_bounds,
        options={'gtol': gtol}
    )

    if not final_result.success:
        return None, None

    return final_result.x, current_points


def fit_braincase(mesh, **settings):
    s = {**BRAINCASE_SETTINGS, **settings}
    v = mesh.vertices
    axis = {'x': 0, 'y': 1, 'z': 2}[s['axis']]
    low, high = mesh.bounds[:, axis]
    rear = v[:, axis] > high - (high - low) * s['rear_fraction']
    if not rear.any():
        return None
    curvature = trimesh.curvature.discrete_mean_curvature_measure(mesh, v, radius=s['curvature_radius'])
    curvature[~rear] = -np.inf
    order = np.argsort(curvature)[::-1]
    selected = np.zeros(len(v), dtype=bool)
    selected[order[:min(s['candidate_count'], int(np.isfinite(curvature).sum()))]] = True
    seed = int(np.argmax(curvature))
    edges = mesh.edges[selected[mesh.edges].all(axis=1)]
    if not len(edges):
        return None
    components = trimesh.graph.connected_components(edges)
    if not len(components):
        return None
    patch = next((np.asarray(list(c)) for c in components if seed in c), None)
    if patch is None:
        patch = np.asarray(list(max(components, key=len)))
    if len(patch) < s['min_patch']:
        return None
    params, inliers = fit_axis_aligned_ellipsoid_iteratively(v[patch], max_iterations=s['max_iterations'],
                                                             outlier_std_dev=s['outlier_std'],
                                                             min_points=s['min_points'], gtol=s['tolerance'])
    if params is None or np.linalg.norm(v[seed] - params[:3]) > s['max_seed_to_centre']:
        return None
    return dict(axes=params[3:6], center=params[:3], inliers=inliers, seed_point=v[seed])


def midline_slope(t, y, n_slices=50):
    edges = np.linspace(t.min(), t.max(), n_slices + 1)
    index = np.clip(np.digitize(t, edges) - 1, 0, n_slices - 1)
    centres, mids = [], []
    for k in range(n_slices):
        in_slice = index == k
        if in_slice.sum() >= 3:
            centres.append(t[in_slice].mean())
            mids.append(0.5 * (y[in_slice].max() + y[in_slice].min()))
    return np.polyfit(centres, mids, 1)[0]


def width_measures(mesh):
    v = mesh.vertices
    low, extent = mesh.bounds[0], mesh.bounding_box.extents
    along = (v[:, 0] - low[0]) / extent[0]
    up = (v[:, 2] - low[2]) / extent[2]
    ends = [int(np.argmax(v[:, 1])), int(np.argmin(v[:, 1]))]
    yaw = np.arctan(midline_slope(v[:, 0], v[:, 1]))
    roll = np.arctan(midline_slope(v[along > 0.5, 2], v[along > 0.5, 1]))
    y_yaw = -v[:, 0] * np.sin(yaw) + v[:, 1] * np.cos(yaw)
    y_yaw_roll = y_yaw * np.cos(roll) - v[:, 2] * np.sin(roll)
    return dict(width_percentile=np.percentile(v[:, 1], 99.5) - np.percentile(v[:, 1], 0.5),
                width_rear_quarter=np.ptp(v[along > 0.75, 1]), width_yaw=np.ptp(y_yaw),
                width_yaw_roll=np.ptp(y_yaw_roll), yaw_deg=np.degrees(yaw), roll_deg=np.degrees(roll),
                width_vertex_along_min=along[ends].min(), width_vertex_along_max=along[ends].max(),
                width_vertex_up_max=up[ends].max())


HC, CARD, RODENT = 'Honeycreepers', 'HC relatives', 'Peromyscus'
FINCH_FOLDER_NAMES = ('DF_and_their_relatives', 'dataset', 'DF_and_their_Relatives', 'Darwins_finches')
OTHER_FOLDERS = [(('Honeycreepers_watertight', 'Honeycreepers_para', 'Honeycreepers'), HC, 42),
                 (('HC_Relatives_watertight', 'HC_Relatives_para', 'HC_Relatives'), CARD, 9),
                 (('Peromyscus', 'Peromyscus_watertight'), RODENT, 2)]
SPECIES_NAMES = {
    'C. flava': 'Chlorodrepanis flava', 'C. stejnegeri': 'Chlorodrepanis stejnegeri',
    'C. virens': 'Chlorodrepanis virens', 'H. wilsoni': 'Hemignathus wilsoni',
    'H. sanguinea': 'Himatione sanguinea', 'L. bailleui': 'Loxioides bailleui',
    'L. caeruleirostris': 'Loxops caeruleirostris', 'L. coccineus': 'Loxops coccineus',
    'M. parva': 'Magumma parva', 'M. mana': 'Manucerthia mana', 'M. phaeosoma': 'Melamprosops phaeosoma',
    'O. bairdi': 'Oreomystis bairdi', 'P. dolei': 'Palmeria dolei', 'P. montana': 'Paroreomyza montana',
    'P. xanthophrys': 'Pseudonestor xanthophrys', 'T. cantans': 'Telespiza cantans',
    'T. ultima': 'Telespiza ultima', 'V. coccinea': 'Vestiaria coccinea',
    'C. erythrinus': 'Carpodacus erythrinus', 'L. arctoa': 'Leucosticte arctoa',
    'L. brandti': 'Leucosticte brandti', 'P. enucleator': 'Pinicola enucleator',
    'P. pyrrhula': 'Pyrrhula pyrrhula',
    'Peromyscus Gossypinua': 'Peromyscus gossypinus', 'Peromyscus Gossypinus': 'Peromyscus gossypinus',
    'Peromyscus Simulus': 'Peromyscus simulus'}
QUALITY = dict(min_inliers=40, max_fit_error=10.0, band_margin=0.05)
ASYMMETRIC = ['Loxops caeruleirostris', 'Loxops coccineus']


def species_of_file(name):
    stem = re.sub(r'_p\d+$', '', os.path.splitext(name)[0]).replace('_', ' ').strip()
    stem = re.sub(r'([A-Z]\.)\s*', r'\1 ', stem)
    stem = re.sub(r'\s*watertight$', '', stem, flags=re.I)
    stem = re.sub(r'[A-Z]$', '', stem).strip()
    return SPECIES_NAMES.get(stem, stem)


def other_specimens(folders):
    rows = []
    for path, group, _ in folders:
        for name in sorted(os.listdir(path)):
            if not name.endswith('.stl'):
                continue
            parameter = re.search(r'_p(\d+)\.stl$', name)
            rows.append(dict(filename=name, path=os.path.join(path, name), group=group,
                             species=species_of_file(name),
                             remeshing_parameter=int(parameter.group(1)) if parameter else np.nan))
    return pd.DataFrame(rows, columns=['filename', 'path', 'group', 'species', 'remeshing_parameter'])


def locate_folder(root, names):
    for place in (root, os.path.join(root, 'dataset_other_taxa'), os.path.join(root, 'dataset'),
                  os.path.dirname(root)):
        for name in names:
            candidate = os.path.join(place, name)
            if os.path.isdir(candidate):
                return candidate
    return None


def find_other_taxa(root):
    found = [(locate_folder(root, names), group, expected) for names, group, expected in OTHER_FOLDERS]
    return [(folder, group, expected) for folder, group, expected in found if folder is not None]


def align_by_principal_axes(mesh):
    vertices = np.asarray(mesh.vertices, float)
    centred = vertices - vertices.mean(axis=0)
    # Match the principal-axis convention used to draw the rodent figures.
    _, eigenvectors = np.linalg.eigh(centred.T @ centred)
    axes = eigenvectors[:, [2, 1, 0]].T
    for axis in range(3):
        if np.sum((centred @ axes[axis]) ** 3) < 0:
            axes[axis] *= -1
    if np.linalg.det(axes) < 0:
        axes[2] *= -1
    oriented = mesh.copy()
    with np.errstate(all='ignore'):
        oriented.vertices = np.ascontiguousarray(centred) @ np.ascontiguousarray(axes.T)
    return oriented


def fit_quality(mesh, fit):
    if fit is None:
        return dict(sphere_radius=np.nan, orbit_inliers=np.nan, fit_error_pct=np.nan, orbit_patch=np.nan,
                    sphere_center_along_pct=np.nan)
    distances = np.linalg.norm(fit['inliers'] - fit['center'], axis=1)
    rms = float(np.sqrt(np.mean((distances - fit['sphere_radius']) ** 2)))
    x_min, length = mesh.bounds[0, 0], mesh.bounding_box.extents[0]
    return dict(sphere_radius=fit['sphere_radius'], orbit_inliers=len(fit['inliers']),
                fit_error_pct=100 * rms / fit['sphere_radius'], orbit_patch=fit.get('patch_size', np.nan),
                sphere_center_along_pct=100 * (fit['center'][0] - x_min) / length)


def reliable(frame):
    return (frame.orbit_inliers >= QUALITY['min_inliers']) & (frame.fit_error_pct <= QUALITY['max_fit_error'])


def flag_reason(row):
    band = ORBIT_SETTINGS['band_start'], ORBIT_SETTINGS['band_end']
    reasons = []
    if np.isfinite(row.sphere_center_along_pct) and min(abs(row.sphere_center_along_pct / 100 - edge)
                                                        for edge in band) < QUALITY['band_margin']:
        reasons.append('sphere centre within 5% of the edge of the search band')
    if row.orbit_inliers < QUALITY['min_inliers']:
        reasons.append(f"fewer than {QUALITY['min_inliers']} inliers")
    if row.fit_error_pct > QUALITY['max_fit_error']:
        reasons.append(f"fit error above {QUALITY['max_fit_error']:.0f}% of the radius")
    return '; '.join(reasons)


def second_orbit(mesh, first):
    if first is None:
        return None
    side = 'left' if first['center'][1] >= 0 else 'right'
    return fit_orbit(mesh, side=side)


def measure_other_skull(path, group, with_second_orbit=True):
    mesh, topology = load_skull(path, align_full_mesh=(group == RODENT))
    record = dict(filename=os.path.basename(path), **skull_dimensions(mesh), **topology)
    orbit = fit_orbit(mesh)
    record.update(fit_quality(mesh, orbit))
    if orbit is not None:
        record.update(sphere_center_x=orbit['center'][0], sphere_center_y=orbit['center'][1],
                      sphere_center_z=orbit['center'][2], orbit_seed_rank=orbit['seed_rank'])
    if with_second_orbit:
        second = fit_quality(mesh, second_orbit(mesh, orbit))
        record.update({f'second_{key}': value for key, value in second.items()})
    return record, dict(mesh=mesh, orbit=orbit)


COLUMNS = ['filename', 'length_x', 'width_y', 'height_z', 'sphere_radius', 'curvature',
           'sphere_center_x', 'sphere_center_y', 'sphere_center_z', 'orbit_inliers', 'orbit_seed_rank',
           'ellipsoid_axis_a', 'ellipsoid_axis_b', 'ellipsoid_axis_c',
           'ellipsoid_center_x', 'ellipsoid_center_y', 'ellipsoid_center_z', 'seconds_orbit', 'seconds_braincase',
           'orbit_patch', 'fit_error_pct', 'sphere_center_along_pct']


def measure_skull(path, extras=False, return_fits=False):
    start = time.perf_counter()
    mesh, topology = load_skull(path)
    record = dict.fromkeys(COLUMNS, np.nan)
    record.update(filename=os.path.basename(path), **skull_dimensions(mesh))
    orbit = fit_orbit(mesh)
    record['seconds_orbit'] = time.perf_counter() - start
    if orbit is not None:
        x, y, z = orbit['center']
        record.update(sphere_radius=orbit['sphere_radius'], curvature=1.0 / orbit['sphere_radius'],
                      sphere_center_x=x, sphere_center_y=y, sphere_center_z=z,
                      orbit_inliers=len(orbit['inliers']), orbit_seed_rank=orbit['seed_rank'])
        record.update({key: value for key, value in fit_quality(mesh, orbit).items()
                       if key in ('fit_error_pct', 'orbit_patch', 'sphere_center_along_pct')})
    start = time.perf_counter()
    braincase = fit_braincase(mesh)
    record['seconds_braincase'] = time.perf_counter() - start
    if braincase is not None:
        (a, b, c), (x, y, z) = braincase['axes'], braincase['center']
        record.update(ellipsoid_axis_a=a, ellipsoid_axis_b=b, ellipsoid_axis_c=c,
                      ellipsoid_center_x=x, ellipsoid_center_y=y, ellipsoid_center_z=z)
    if extras:
        record.update(topology)
        record.update(width_measures(mesh))
        record['vertex_spacing'] = float(mesh.edges_unique_length.mean())
        second = fit_quality(mesh, second_orbit(mesh, orbit))
        record.update({f'second_{key}': value for key, value in second.items()})
    return (record, dict(mesh=mesh, orbit=orbit, braincase=braincase)) if return_fits else record


def _pyvista():
    try:
        import pyvista
    except ImportError as error:
        raise ImportError('Showing the fits needs pyvista. In PyCharm: Settings > Project > Python Interpreter > '
                          '+ > pyvista > Install Package.') from error
    return pyvista


def show_orbit_fit(mesh, fit, title=''):
    pv = _pyvista()
    plotter = pv.Plotter()
    plotter.add_text(title, position='upper_left', font_size=12, color='black')
    plotter.add_mesh(mesh, style='surface', opacity=0.4, color='lightgrey')
    plotter.add_mesh(pv.Sphere(radius=fit['sphere_radius'], center=fit['center']), style='wireframe', color='blue',
                     line_width=2)
    plotter.add_points(fit['inliers'], color='crimson', point_size=6, render_points_as_spheres=True,
                       label='Selected Points (Inliers)')
    plotter.add_points(fit['seed_point'], color='lime', point_size=15, render_points_as_spheres=True, label='Seed Point')
    plotter.add_legend()
    plotter.show()


def show_braincase_fit(mesh, fit, title=''):
    pv = _pyvista()
    plotter = pv.Plotter()
    plotter.add_text(title, position='upper_left', font_size=12, color='black')
    plotter.add_mesh(mesh, style='surface', opacity=0.3, color='lightgrey')
    ellipsoid = pv.Sphere(radius=1.0, theta_resolution=30, phi_resolution=30)
    ellipsoid.points = ellipsoid.points * fit['axes']
    ellipsoid.points += fit['center']
    plotter.add_mesh(ellipsoid, style='wireframe', color='blue', line_width=2)
    plotter.add_points(fit['inliers'], color='crimson', point_size=6, render_points_as_spheres=True,
                       label='Selected Inlier Points')
    plotter.add_points(fit['seed_point'], color='lime', point_size=15, render_points_as_spheres=True, label='Seed Point')
    for i, (colour, name) in enumerate(zip(['red', 'green', 'blue'], ['X Axis', 'Y Axis', 'Z Axis'])):
        direction = np.zeros(3)
        direction[i] = 1.0
        semi_axis = fit['axes'][i]
        plotter.add_mesh(pv.Line(fit['center'] - direction * semi_axis, fit['center'] + direction * semi_axis),
                         color=colour, line_width=5, label=f'{name} ({semi_axis:.2f})')
    plotter.add_legend()
    plotter.show()


def verdict(counts):
    total, agree, differ = int(sum(counts)), int(counts.get('yes', 0)), int(counts.get('NO', 0))
    source = ('from Dataset.xlsx (quick run; the meshes were not refitted)' if QUICK_RUN else
              f'from the {MEASURED_MESHES} skull meshes')
    if agree == total:
        return f'All {total} encoded numerical comparisons passed using measurements {source}.'
    problems = ([f"{differ} {'differs' if differ == 1 else 'differ'}"] if differ else [])
    problems += [f'{total - agree - differ} could not be computed'] if total - agree - differ else []
    return f"{agree} of {total} encoded numerical comparisons passed using measurements {source}; {' and '.join(problems)}."


def agrees(reported, value, tolerance=None):
    if value is None or not np.isfinite(float(value)):
        return None, 'not computed'
    value, text = float(value), str(reported).strip()
    if text.startswith('>='):
        return value >= float(text[2:]), f'{value:.1f}'
    if text.startswith('<='):
        limit = text[2:]
        decimals = len(limit.split('.')[1]) if '.' in limit else 0
        return value < float(limit) + 0.5 * 10 ** -decimals, f'{value:.{decimals + 1}f}'
    if text.startswith('<'):
        return value < float(text[1:]), f'{value:.2g}'
    scientific = re.fullmatch(r'(-?\d+)(?:\.(\d+))?e(-?\d+)', text)
    if scientific:
        decimals = len(scientific.group(2) or '')
        unit = 10.0 ** (int(scientific.group(3)) - decimals)
        return abs(value - float(text)) <= 0.5 * unit * (1 + 1e-9), f'{value:.{decimals}e}'
    decimals = len(text.split('.')[1]) if '.' in text else 0
    limit = tolerance if tolerance is not None else 0.5 * 10 ** -decimals + 1e-9
    return abs(value - float(text)) <= limit, f'{value:.{decimals}f}'


def md(text):
    return str(text).replace('|', '\\|')


class Report:
    def __init__(self, out):
        self.out = out
        self.items = []
        self.tables = {}
        self.section_title = ''

    def section(self, title):
        self.section_title = title
        self.items.append(('section', title))

    def note(self, text):
        self.items.append(('note', text))

    def check(self, quantity, reported, value, tolerance=None):
        ok, shown = agrees(reported, value, tolerance)
        row = dict(section=self.section_title, quantity=quantity, reported=str(reported), reproduced=shown,
                   full_precision='' if value is None or not np.isfinite(float(value)) else f'{float(value):.10g}',
                   agrees={True: 'yes', False: 'NO', None: 'not computed'}[ok])
        self.items.append(('check', row))

    def table(self, title, row_labels, column_labels, reported, values, csv_name):
        shown = pd.DataFrame('', index=row_labels, columns=column_labels)
        for i, r in enumerate(row_labels):
            for j, c in enumerate(column_labels):
                if reported[i][j] is None:
                    shown.loc[r, c] = '-'
                    continue
                ok, text = agrees(reported[i][j], values[i][j])
                shown.loc[r, c] = text if ok else f'**{text}** (paper {reported[i][j]})'
                self.items.append(('cell', dict(section=self.section_title, quantity=f'{title}: {r} / {c}',
                                                reported=str(reported[i][j]), reproduced=text,
                                                full_precision=f'{float(values[i][j]):.10g}',
                                                agrees={True: 'yes', False: 'NO', None: 'not computed'}[ok])))
        pd.DataFrame(values, index=row_labels, columns=column_labels).to_csv(os.path.join(self.out, 'tables', csv_name))
        number = csv_name[len('Table'):-len('.csv')]
        self.tables[number] = dict(rows=list(row_labels), reported=reported, values=values)
        self.items.append(('table', title, shown, number))

    def rows(self):
        return [item[1] for item in self.items if item[0] in ('check', 'cell')]

    def write(self, header, models=None):
        rows = pd.DataFrame(self.rows())
        rows.to_csv(os.path.join(self.out, 'values.csv'), index=False)
        counts = rows.agrees.value_counts()
        agree = int(counts.get('yes', 0))
        summary = rows.groupby('section', sort=False)['agrees'].agg(numbers='size', agree=lambda a: int((a == 'yes').sum()))
        lines = header + ['', f'**{verdict(counts)}**', '', '| Part of the paper | Numbers | Reproduced |', '|---|---|---|']
        lines += [f'| {md(section)} | {r.numbers} | {r.agree} |' for section, r in summary.iterrows()]
        lines += [f'| **Total** | **{len(rows)}** | **{agree}** |', '']
        differing = rows[rows.agrees == 'NO']
        if len(differing):
            lines += ['## Numbers that differ from the manuscript', '', '| Where | Quantity | Paper | Reproduced |',
                      '|---|---|---|---|']
            lines += [f"| {md(r.section)} | {md(r.quantity)} | {md(r.reported)} | {r.reproduced} |" for r in differing.itertuples()]
        in_checks = False
        for item in self.items:
            if item[0] == 'check':
                if not in_checks:
                    lines += ['', '| Quantity | Paper | Reproduced | Agrees |', '|---|---|---|---|']
                    in_checks = True
                r = item[1]
                lines.append(f"| {md(r['quantity'])} | {md(r['reported'])} | {r['reproduced']} | {r['agrees']} |")
                continue
            if item[0] == 'cell':
                continue
            in_checks = False
            if item[0] == 'section':
                lines += ['', f'## {item[1]}']
            elif item[0] == 'note':
                lines += ['', item[1]]
            elif item[0] == 'table' and models and item[3] in models:
                lines += [''] + markdown_table(models[item[3]])
            elif item[0] == 'table':
                frame = item[2]
                lines += ['', f'**{item[1]}**', '', '| | ' + ' | '.join(frame.columns) + ' |',
                          '|---' * (len(frame.columns) + 1) + '|']
                lines += [f'| {label} | ' + ' | '.join(frame.loc[label]) + ' |' for label in frame.index]
        with open(os.path.join(self.out, 'report.md'), 'w', encoding='utf-8') as handle:
            handle.write('\n'.join(lines) + '\n')
        return counts


def spearman(a, b):
    return stats.spearmanr(np.asarray(a, float), np.asarray(b, float))


def one_way_anova(values, groups):
    values, groups = np.asarray(values, float), np.asarray(groups)
    samples = [values[groups == g] for g in pd.unique(groups)]
    F, p = stats.f_oneway(*samples)
    grand = values.mean()
    eta2 = sum(len(s) * (s.mean() - grand) ** 2 for s in samples) / ((values - grand) ** 2).sum()
    return F, p, eta2, len(samples) - 1, len(values) - len(samples)


def correlation_matrix(D, mask, rows, columns, method):
    return [[D.loc[mask, r].corr(D.loc[mask, c], method=method) for c in columns] for r in rows]


def run_statistics(D, specimens, full, rep):
    D = D.copy()
    D['curvature'] = 1.0 / D.sphere_radius
    D['L'] = (D.length_x * D.width_y * D.height_z) ** (1 / 3)
    D['kappa'] = D.L / D.sphere_radius
    D['c_over_b'] = D.ellipsoid_axis_c / D.ellipsoid_axis_b
    D['x_over_y'] = D.length_x / D.width_y
    finch, relative = (D.group == DF).values, (D.group == REL).values
    groups = {"Darwin's finches": finch, 'DF relatives': relative, 'All': np.ones(len(D), bool)}
    wide = D.species.isin(WIDE_SPECIES).values

    rep.section('Materials and Methods: dataset and mesh processing')
    rep.check('Specimens', '100', len(D))
    rep.check("Darwin's finches (SI Table S1)", '53', finch.sum())
    rep.check('Relatives (SI Table S2)', '47', relative.sum())
    rep.check('Genera', '11', D.genus.nunique())
    changed = specimens.remeshing_parameter != 60
    rep.check('Remeshing parameter kept at the default of 60', '59', (~changed).sum())
    rep.check('Remeshing parameter changed', '41', changed.sum())
    rep.check('Smallest changed value', '30', specimens.remeshing_parameter[changed].min())
    rep.check('Largest changed value', '75', specimens.remeshing_parameter[changed].max())
    rep.note('The remeshing parameters are those of SI Tables S1-S2, written into this file (SPECIES); the '
             'remeshing itself is not rerun.')
    if full:
        rep.check('Remeshed meshes that are closed surfaces', '100', D.closed.sum())
        rep.check('Largest component of genus at least 1', '63', (D.genus_largest >= 1).sum())
        rep.check('Meshes with disconnected fragments', '27', (D.n_components > 1).sum())
        rep.check('Single-component, genus-0 meshes', '37', ((D.n_components == 1) & (D.genus_largest == 0)).sum())
        pallidus = D.genus_largest[D.species == 'pallidus']
        rep.check('C. pallidus: smallest genus', '0', pallidus.min())
        rep.check('C. pallidus: largest genus', '2', pallidus.max())

    rep.section('Materials and Methods: fitting settings stated in the text, as found in the code')
    So, Sb = ORBIT_SETTINGS, BRAINCASE_SETTINGS
    rep.check('Orbit search band starts at this fraction of the length (middle 40%)', '0.30', So['band_start'])
    rep.check('Orbit search band ends at this fraction of the length', '0.70', So['band_end'])
    rep.check('Braincase region: rear fraction of the length', '0.40', Sb['rear_fraction'])
    rep.check('Sphere fit: outlier threshold (SD above the mean error)', '2.0', So['outlier_std'])
    rep.check('Sphere fit: maximum refinement steps', '3', So['max_iterations'])
    rep.check('Sphere fit: minimum number of points', '4', So['min_points'])
    rep.check('Ellipsoid fit: outlier threshold (SD above the mean error)', '1.5', Sb['outlier_std'])
    rep.check('Ellipsoid fit: maximum refinement steps', '3', Sb['max_iterations'])
    rep.check('Ellipsoid fit: minimum number of points', '6', Sb['min_points'])
    rep.check('Sphere fit: convergence tolerance of L-BFGS-B (gtol)', '1e-5', So['tolerance'])
    rep.check('Ellipsoid fit: convergence tolerance of L-BFGS-B (gtol)', '1e-5', Sb['tolerance'])
    rep.check('Smallest concave component a sphere is fitted to (vertices)', '20', So['min_patch'])
    rep.check('Vertices of the posterior region used for the braincase', '1200', Sb['candidate_count'])
    rep.check('Accepted radius range, lower end (mm)', '2', So['min_radius'])
    rep.check('Accepted radius range, upper end (mm)', '6', So['max_radius'])
    rep.check('Smallest orbit radius of the finch specimens (mm)', '2.35', D.sphere_radius.min())
    rep.check('Largest orbit radius of the finch specimens (mm)', '5.85', D.sphere_radius.max())
    if full:
        rep.check('Mean distance between neighbouring vertices of the remeshed surfaces (mm)', '0.8',
                  D.vertex_spacing.mean(), tolerance=0.05)
    rep.note(f"Other settings used by the code. Orbit: curvature neighbourhood radius {So['curvature_radius']} mm, "
             f"{So['candidate_count']} candidate vertices, accepted radius between {So['min_radius']} and "
             f"{So['max_radius']} mm, up to {So['max_seeds']} seeds, patches of at least "
             f"{So['min_patch']} vertices. Braincase: curvature neighbourhood radius {Sb['curvature_radius']} mm, "
             f"{Sb['candidate_count']} candidate vertices, patches of at least {Sb['min_patch']} vertices, "
             f"seed-to-centre distance at most {Sb['max_seed_to_centre']} mm.")
    fewest = Sb['min_patch']
    for _ in range(Sb['max_iterations'] - 1):
        fewest -= int(fewest / (1 + Sb['outlier_std'] ** 2))
    if fewest > Sb['min_points']:
        rep.note(f"The ellipsoid fit never reaches its limit of {Sb['min_points']} points. A fit starts from at least "
                 f"{Sb['min_patch']} points, and one outlier step at {Sb['outlier_std']} SD removes at most a fraction "
                 f"1/(1 + {Sb['outlier_std']}^2) of them (Cantelli's inequality), so at least {fewest} points remain "
                 f"at every check. The limit therefore never changes a fit.")

    rep.section('Results: expected scaling between skull size and orbit radius (Fig. 9)')
    printed = {"Darwin's finches": ['0.740', '0.802', '0.775'], 'DF relatives': ['0.712', '0.863', '0.902'],
               'All': ['0.759', '0.838', '0.848']}
    for group, values in printed.items():
        for dim, value in zip(DIMS, values):
            rep.check(f'Spearman, sphere radius vs {dim} ({group})', value,
                      spearman(D.sphere_radius[groups[group]], D[dim][groups[group]])[0])
    rows, columns = ['Length x', 'Width y', 'Height z'], list(groups)
    tables = [('SI Table S3: Pearson, 1/(orbit curvature)', 'sphere_radius', 'pearson', 'TableS3.csv',
               [['0.711353', '0.665122', '0.722874'], ['0.773172', '0.823192', '0.807400'], ['0.760901', '0.856100', '0.821904']]),
              ('SI Table S4: Spearman, 1/(orbit curvature)', 'sphere_radius', 'spearman', 'TableS4.csv',
               [['0.739881', '0.712188', '0.759376'], ['0.801726', '0.862858', '0.837996'], ['0.774552', '0.902058', '0.848425']]),
              ('SI Table S5: Pearson, orbit curvature', 'curvature', 'pearson', 'TableS5.csv',
               [['-0.735185', '-0.682898', '-0.745167'], ['-0.763031', '-0.818753', '-0.799828'], ['-0.752412', '-0.870089', '-0.831688']]),
              ('SI Table S6: Spearman, orbit curvature', 'curvature', 'spearman', 'TableS6.csv',
               [['-0.739881', '-0.712188', '-0.759376'], ['-0.801726', '-0.862858', '-0.837996'], ['-0.774552', '-0.902058', '-0.848425']])]
    for title, target, method, csv_name, reported in tables:
        values = [[D.loc[groups[g], target].corr(D.loc[groups[g], dim], method=method) for g in columns] for dim in DIMS]
        rep.table(title, rows, columns, reported, values, csv_name)

    rep.section('Results: the width gap (Fig. 9; SI Section S2, Tables S7-S8)')
    rep.check('G. magnirostris: smallest width (mm)', '23.11', D.width_y[finch & wide].min())
    rep.check('G. magnirostris: largest width (mm)', '24.27', D.width_y[finch & wide].max())
    rep.check('Other Darwin\'s finches: largest width (mm)', '20.15', D.width_y[finch & ~wide].max())
    rep.check('L. violacea and L. portoricensis: smallest width (mm)', '17.49', D.width_y[relative & wide].min())
    rep.check('L. violacea and L. portoricensis: largest width (mm)', '19.42', D.width_y[relative & wide].max())
    rep.check('Other relatives: largest width (mm)', '15.20', D.width_y[relative & ~wide].max())
    rep.check('Specimens beyond the gap among Darwin\'s finches', '5', (finch & wide).sum())
    rep.check('Specimens beyond the gap among the relatives', '10', (relative & wide).sum())
    s7_rows = [('Bounding-box width y', 'width_y', ['23.11', '20.15', '2.96', '17.49', '15.20', '2.28']),
               ('99.5th-0.5th percentile width', 'width_percentile', ['22.61', '19.58', '3.04', '16.97', '15.08', '1.89']),
               ('Width of the posterior quarter', 'width_rear_quarter', ['23.11', '20.15', '2.96', '16.92', '15.20', '1.72']),
               ('Width after removing residual yaw', 'width_yaw', ['23.11', '20.16', '2.95', '17.49', '15.21', '2.28']),
               ('Bounding-box height z', 'height_z', ['19.87', '19.17', '0.69', '16.99', '15.32', '1.68']),
               ('Bounding-box length x', 'length_x', ['36.00', '35.97', '0.04', '31.34', '31.28', '0.06'])]
    s7_rows = [row for row in s7_rows if row[1] in D.columns]
    values = []
    for _, column, _ in s7_rows:
        line = []
        for group in (finch, relative):
            smallest, largest_other = D.loc[group & wide, column].min(), D.loc[group & ~wide, column].max()
            line += [smallest, largest_other, smallest - largest_other]
        values.append(line)
    rep.table('SI Table S7: widest specimens (mm)', [r[0] for r in s7_rows],
              ["DF: min", "DF: others", "DF: gap", 'Relatives: min', 'Relatives: others', 'Relatives: gap'],
              [r[2] for r in s7_rows], values, 'TableS7.csv')
    if full:
        rep.note('Rows 2-4 of Table S7 and the residual yaw follow SI Section S2: percentiles of the vertex '
                 'y-coordinates; vertices beyond 75% of the length from the beak tip; residual yaw from a straight line '
                 'fitted in dorsal view to the midpoints of the width of 50 equal slices along the skull length.')
        rep.check('Width vertices: smallest position along the length (% from the beak tip)', '64',
                  100 * D.width_vertex_along_min.min())
        rep.check('Width vertices: largest position along the length (% from the beak tip; text: between 64% and 85%)',
                  '<=85', 100 * D.width_vertex_along_max.max())
        rep.check('Wide specimens with both width vertices below 36% of the height', '14',
                  ((D.width_vertex_up_max < 0.36) & wide).sum())
        rep.check('Largest residual yaw of the 15 wide specimens (degrees)', '<=1.2', D.yaw_deg[wide].abs().max())

    without = {g: m & ~wide for g, m in groups.items()}
    values, reported = [], [['0.740', '0.690', '0.712', '0.485', '0.759', '0.695'],
                            ['0.802', '0.757', '0.863', '0.766', '0.838', '0.784'],
                            ['0.775', '0.721', '0.902', '0.840', '0.848', '0.802']]
    for dim in DIMS:
        line = []
        for g in groups:
            line += [spearman(D.sphere_radius[groups[g]], D[dim][groups[g]])[0],
                     spearman(D.sphere_radius[without[g]], D[dim][without[g]])[0]]
        values.append(line)
    rep.table('SI Table S8: Spearman, sphere radius, all specimens and without the three widest species', rows,
              ['DF: all', 'DF: without', 'Relatives: all', 'Relatives: without', 'All: all', 'All: without'],
              reported, values, 'TableS8.csv')
    rep.check("Specimens without the three species: Darwin's finches", '48', without["Darwin's finches"].sum())
    rep.check('Specimens without the three species: relatives', '37', without['DF relatives'].sum())
    rep.check('Specimens without the three species: all', '85', without['All'].sum())
    remaining = [values[1][1], values[2][1], values[1][3], values[2][3]]
    rep.check('Without the three species, width and height: smallest correlation', '0.72', min(remaining))
    rep.check('Without the three species, width and height: largest correlation', '0.84', max(remaining))
    flaveola, canora = D[D.species == 'flaveola'], D[D.species == 'canora']
    rep.check('C. flaveola longer than T. canora (%, "about 30%")', '30',
              100 * (flaveola.length_x.mean() / canora.length_x.mean() - 1), tolerance=5)
    rep.note(f"C. flaveola / T. canora: width ratio {flaveola.width_y.mean() / canora.width_y.mean():.2f}, "
             f"height ratio {flaveola.height_z.mean() / canora.height_z.mean():.2f} (text: same width and height).")

    rep.section('Results: curvature model, Eq. (8), and SI Table S11')
    train = (D.Model == 'Training').values
    test = ~train
    rep.check('Training specimens', '50', train.sum())
    rep.check('Test specimens', '50', test.sum())
    X = sm.add_constant(D[DIMS].astype(float))
    y = D.curvature.astype(float)
    model = sm.OLS(y[train], X[train]).fit()
    for name, printed_value, value in zip(['intercept', 'x', 'y', 'z'], ['0.5653', '-0.0013', '-0.0004', '-0.0153'], model.params):
        rep.check(f'Eq. (8): coefficient of {name}', printed_value, value)
    pairwise = D.loc[train, DIMS].corr().values[np.triu_indices(3, 1)]
    rep.check('Pearson r among x, y, z (training set): smallest', '0.75', pairwise.min())
    rep.check('Pearson r among x, y, z (training set): largest', '0.95', pairwise.max())
    for dim, printed_value in zip(DIMS, ['3.3', '14.9', '10.8']):
        others = [d for d in DIMS if d != dim]
        r2 = sm.OLS(D.loc[train, dim], sm.add_constant(D.loc[train, others])).fit().rsquared
        rep.check(f'Variance inflation factor of {dim}', printed_value, 1 / (1 - r2))
    for name, column, printed_min, printed_max in [('Length x', 'length_x', '20.22', '37.78'),
                                                   ('Width y', 'width_y', '12.23', '24.27'),
                                                   ('Height z', 'height_z', '11.03', '23.01')]:
        rep.check(f'{name}: smallest in the dataset (mm)', printed_min, D[column].min())
        rep.check(f'{name}: largest in the dataset (mm)', printed_max, D[column].max())
    rep.check('F-test p-value of Eq. (8)', '6.81e-8', model.f_pvalue)
    printed_model = model.params.round(4)
    prediction = X @ printed_model
    error = ((prediction - y).abs() / y)[test]
    r2_test = np.corrcoef(y[test], prediction[test])[0, 1] ** 2
    rep.check('R2_test: squared correlation, 50 test specimens', '0.8636', r2_test)
    rep.check('Abstract: share of the variance in curvature (%)', '86.36', 100 * r2_test)
    rep.check('Mean relative error on the test specimens (%)', '6.14', 100 * error.mean())
    rep.check('Smallest relative error (%)', '0.064', 100 * error.min())
    rep.check('Largest relative error (%)', '27.93', 100 * error.max())
    rep.check('Test specimens with relative error below 10%', '39', (error < 0.10).sum())
    rep.check('Test specimens with relative error below 5%', '28', (error < 0.05).sum())
    rep.check('Test specimens with relative error below 1%', '13', (error < 0.01).sum())
    rep.note('The test-set quantities of Eq. (8) use its coefficients as printed (four decimals), as stated in the '
             'caption of SI Table S11.')
    table_rows, reported, values = ['x, y, z jointly (Eq. 8)'], [[None, None, '0.864', '6.14']], [[np.nan, np.nan, r2_test, 100 * error.mean()]]
    for label, column, b0, b1, r2_printed, mre_printed in [('L = (xyz)^(1/3)', 'L', '0.5767', '-0.0151', '0.850', '6.15'),
                                                            ('z (height)', 'height_z', '0.5521', '-0.0173', '0.849', '6.66'),
                                                            ('y (width)', 'width_y', '0.5543', '-0.0166', '0.776', '8.16'),
                                                            ('x (length)', 'length_x', '0.5294', '-0.0085', '0.755', '8.32')]:
        single = sm.OLS(y[train], sm.add_constant(D.loc[train, [column]].astype(float))).fit()
        predicted = single.predict(sm.add_constant(D.loc[test, [column]].astype(float)))
        table_rows.append(label)
        reported.append([b0, b1, r2_printed, mre_printed])
        values.append([single.params.iloc[0], single.params.iloc[1], np.corrcoef(y[test], predicted)[0, 1] ** 2,
                       100 * ((predicted - y[test]).abs() / y[test]).mean()])
    rep.table('SI Table S11: prediction of the orbit curvature from the skull dimensions', table_rows,
              ['intercept', 'slope', 'R2_test', 'MRE (%)'], reported, values, 'TableS11.csv')

    rep.section('Results: size-independent descriptors (Figs. 11-12; SI Tables S9-S10)')
    for label, mask, printed_rho, printed_p in [('all 100 specimens', groups['All'], '-0.05', '0.59'),
                                                ("Darwin's finches", finch, '-0.14', '0.33'),
                                                ('relatives', relative, '-0.05', '0.75')]:
        rho, p = spearman(D.kappa[mask], D.L[mask])
        rep.check(f'Normalized curvature vs L, Spearman rho ({label})', printed_rho, rho)
        rep.check(f'Normalized curvature vs L, p ({label})', printed_p, p)
    F, p, eta2, df1, df2 = one_way_anova(D.kappa, D.genus)
    rep.check('Normalized curvature across genera: numerator degrees of freedom', '10', df1)
    rep.check('Normalized curvature across genera: denominator degrees of freedom', '89', df2)
    rep.check('Normalized curvature across genera: F', '3.62', F)
    rep.check('Normalized curvature across genera: p (main text, p < 0.001)', '<0.001', p)
    rep.check('Normalized curvature across genera: eta^2', '0.289', eta2)
    size_variables = [('L = (xyz)^(1/3)', D.L, ['-0.05', '0.59', '3.62', '4.5e-4', '0.289']),
                      ('x (length)', D.length_x, ['-0.10', '0.31', '6.71', '1.1e-7', '0.430']),
                      ('y (width)', D.width_y, ['-0.11', '0.29', '3.18', '1.6e-3', '0.263']),
                      ('z (height)', D.height_z, ['-0.02', '0.84', '3.14', '1.8e-3', '0.261']),
                      ('(abc)^(1/3) (ellipsoid)', (D.ellipsoid_axis_a * D.ellipsoid_axis_b * D.ellipsoid_axis_c) ** (1 / 3),
                       ['-0.11', '0.27', '1.84', '0.064', '0.172'])]
    values = []
    for _, size, _ in size_variables:
        ratio = size / D.sphere_radius
        rho, p_rho = spearman(ratio, D.L)
        F, p_F, eta2, _, _ = one_way_anova(ratio, D.genus)
        values.append([rho, p_rho, F, p_F, eta2])
    rep.table('SI Table S9: normalized orbit curvature S/r for other size variables', [s[0] for s in size_variables],
              ['Spearman rho with L', 'p', 'F', 'p', 'eta^2'], [s[2] for s in size_variables], values, 'TableS9.csv')
    rep.check('Other size variables: largest |rho| with L (text: |rho| <= 0.12)', '<=0.12', max(abs(v[0]) for v in values[1:]))
    rep.check('Other size variables: smallest eta^2', '0.17', min(v[4] for v in values[1:]))
    rep.check('Other size variables: largest eta^2', '0.43', max(v[4] for v in values[1:]))
    for label, column, printed in [('c/b', 'c_over_b', ['14.016', '1.6e-14', '0.612']),
                                   ('x/y', 'x_over_y', ['14.021', '1.6e-14', '0.612'])]:
        F, p, eta2, _, _ = one_way_anova(D[column], D.genus)
        rep.check(f'{label} across genera: F', printed[0], F)
        rep.check(f'{label} across genera: p', printed[1], p)
        rep.check(f'{label} across genera: eta^2', printed[2], eta2)
    rep.check('Spearman rho between c/b and x/y', '0.07', spearman(D.c_over_b, D.x_over_y)[0])
    rep.check("c/b vs L within Darwin's finches, Spearman rho", '0.36', spearman(D.c_over_b[finch], D.L[finch])[0])
    rep.check('c/b vs L within the relatives, Spearman rho', '0.70', spearman(D.c_over_b[relative], D.L[relative])[0])
    pooled = max(abs(spearman(D[c], D.L)[0]) for c in ['kappa', 'c_over_b', 'x_over_y'])
    rep.check('Fig. 12 caption: largest |rho| of the three descriptors with L, pooled sample', '<=0.12', pooled)

    printed_s10 = {'Camarhynchus': ['13', '5.74', '0.66', '0.92', '0.02', '1.74', '0.14', '19.44', '1.47'],
                   'Certhidea': ['5', '5.21', '0.37', '0.87', '0.02', '1.86', '0.06', '16.40', '0.35'],
                   'Geospiza': ['29', '5.30', '0.53', '0.93', '0.03', '1.76', '0.14', '21.62', '2.95'],
                   'Pinaroloxias': ['2', '5.70', '0.07', '0.96', '0.02', '2.00', '0.00', '17.49', '0.13'],
                   'Platyspiza': ['4', '4.53', '0.41', '1.00', '0.01', '1.70', '0.04', '21.53', '0.38'],
                   'Coereba': ['5', '5.93', '0.68', '0.95', '0.02', '2.11', '0.02', '16.23', '0.31'],
                   'Euneornis': ['5', '5.42', '0.09', '0.97', '0.01', '2.11', '0.03', '18.04', '0.50'],
                   'Loxigilla': ['14', '5.21', '0.53', '1.01', '0.03', '1.80', '0.08', '21.08', '1.75'],
                   'Loxipasser': ['5', '5.16', '0.15', '0.99', '0.03', '1.77', '0.02', '16.13', '0.22'],
                   'Melopyrrha': ['4', '4.60', '0.50', '0.99', '0.03', '1.84', '0.04', '18.14', '0.29'],
                   'Tiaris': ['14', '5.24', '0.45', '0.94', '0.05', '1.66', '0.07', '15.15', '0.70']}
    values = []
    for genus in GENERA:
        g = D[D.genus == genus]
        line = [len(g)]
        for column in ['kappa', 'c_over_b', 'x_over_y', 'L']:
            line += [g[column].mean(), g[column].std()]
        values.append(line)
    rep.table('SI Table S10: genus means and SDs', GENERA,
              ['n', 'kappa mean', 'kappa SD', 'c/b mean', 'c/b SD', 'x/y mean', 'x/y SD', 'L mean', 'L SD'],
              [printed_s10[g] for g in GENERA], values, 'TableS10.csv')

    rep.section('Results: neurocranial geometry (SI Tables S12-S17)')
    D['one_over_curvature'] = D.sphere_radius
    variables = ['ellipsoid_axis_a', 'ellipsoid_axis_b', 'ellipsoid_axis_c', 'one_over_curvature', 'curvature']
    columns = DIMS + ['one_over_curvature', 'curvature']
    labels_rows = ['Semi-axis a', 'Semi-axis b', 'Semi-axis c', '1/Curvature', 'Curvature']
    labels_columns = ['Length x', 'Width y', 'Height z', '1/Curvature', 'Curvature']
    printed_tables = {
        ('S12', DF, 'pearson'): [['0.87', '0.93', '0.89', '0.69', '-0.70'], ['0.79', '0.87', '0.83', '0.62', '-0.63'],
                                 ['0.76', '0.84', '0.84', '0.61', '-0.63'], ['0.71', '0.77', '0.76', '1.00', '-0.98'],
                                 ['-0.74', '-0.76', '-0.75', '-0.98', '1.00']],
        ('S13', DF, 'spearman'): [['0.90', '0.91', '0.83', '0.74', '-0.74'], ['0.88', '0.97', '0.90', '0.82', '-0.82'],
                                  ['0.87', '0.97', '0.93', '0.82', '-0.82'], ['0.74', '0.80', '0.77', '1.00', '-1.00'],
                                  ['-0.74', '-0.80', '-0.77', '-1.00', '1.00']],
        ('S14', REL, 'pearson'): [['0.55', '0.65', '0.63', '0.51', '-0.55'], ['0.78', '0.95', '0.94', '0.82', '-0.83'],
                                  ['0.82', '0.98', '0.98', '0.84', '-0.86'], ['0.67', '0.82', '0.86', '1.00', '-0.97'],
                                  ['-0.68', '-0.82', '-0.87', '-0.97', '1.00']],
        ('S15', REL, 'spearman'): [['0.81', '0.89', '0.84', '0.80', '-0.80'], ['0.79', '0.96', '0.94', '0.88', '-0.88'],
                                   ['0.81', '0.95', '0.96', '0.90', '-0.90'], ['0.71', '0.86', '0.90', '1.00', '-1.00'],
                                   ['-0.71', '-0.86', '-0.90', '-1.00', '1.00']],
        ('S16', 'All', 'pearson'): [['0.73', '0.80', '0.78', '0.63', '-0.66'], ['0.81', '0.92', '0.89', '0.72', '-0.73'],
                                    ['0.80', '0.89', '0.90', '0.73', '-0.75'], ['0.72', '0.81', '0.82', '1.00', '-0.97'],
                                    ['-0.75', '-0.80', '-0.83', '-0.97', '1.00']],
        ('S17', 'All', 'spearman'): [['0.85', '0.91', '0.89', '0.77', '-0.77'], ['0.84', '0.97', '0.95', '0.84', '-0.84'],
                                     ['0.86', '0.95', '0.96', '0.86', '-0.86'], ['0.76', '0.84', '0.85', '1.00', '-1.00'],
                                     ['-0.76', '-0.84', '-0.85', '-1.00', '1.00']]}
    masks = {DF: finch, REL: relative, 'All': groups['All']}
    for (number, group, method), reported in printed_tables.items():
        rep.table(f'SI Table {number}: {method.capitalize()}, {group}', labels_rows, labels_columns, reported,
                  correlation_matrix(D, masks[group], variables, columns, method), f'Table{number}.csv')

    rep.section('Discussion')
    if full:
        rep.check('Median number of inlier points per orbit', '112', D.orbit_inliers.median())
        rep.note(f"Computation time on this machine: {D.seconds_orbit.mean():.1f} s (orbit) and "
                 f"{D.seconds_braincase.mean():.1f} s (braincase) per specimen. The paper reports 1.6 s and 1.7 s on "
                 f"an Intel Xeon (2.10 GHz); timings depend on the hardware and are not compared.")
    else:
        rep.note('Inlier counts and timings require the full run.')


def run_other_taxa_statistics(O, D, full, rep):
    O = O.copy()
    birds = O[O.group != RODENT].copy()
    birds['L'] = (birds.length_x * birds.width_y * birds.height_z) ** (1 / 3)
    birds['curvature'] = 1.0 / birds.sphere_radius
    birds['ok'] = reliable(birds)
    good = birds[birds.ok]
    finch = D.copy()
    finch['L'] = (finch.length_x * finch.width_y * finch.height_z) ** (1 / 3)

    rep.section('SI Section S4: the skulls outside the finch dataset (main text: second avian radiation)')
    rep.check('Skulls outside the finch dataset', '51', len(birds))
    rep.check('Avian skulls of the study (Fig. 13)', '151', len(birds) + len(finch))
    rep.check('Hawaiian honeycreepers', '42', (birds.group == HC).sum())
    rep.check('Species of honeycreepers', '18', birds.species[birds.group == HC].nunique())
    rep.check('Cardueline relatives', '9', (birds.group == CARD).sum())
    rep.check('Species of cardueline relatives', '5', birds.species[birds.group == CARD].nunique())
    rep.check('Skulls on which the sphere fit converged', '51', birds.sphere_radius.notna().sum())
    rep.check('Inliers: smallest', '19', birds.orbit_inliers.min())
    rep.check('Inliers: largest', '138', birds.orbit_inliers.max())
    rep.check('Inliers: median', '76', birds.orbit_inliers.median())
    rep.check('Fit error: median (% of the radius)', '5.8', birds.fit_error_pct.median())
    if full:
        rep.check('Finch specimens, inliers: smallest', '21', finch.orbit_inliers.min())
        rep.check('Finch specimens, inliers: largest', '163', finch.orbit_inliers.max())
        rep.check('Finch specimens, inliers: median', '112', finch.orbit_inliers.median())
        rep.check('Finch specimens, fit error: median (%)', '5.4', finch.fit_error_pct.median())
        rep.check('Finch specimens, fit error: 95th percentile (%)', '8.9', finch.fit_error_pct.quantile(0.95))
        rep.check('Inlier criterion, close to the 5th percentile of the finch specimens', '40',
                  finch.orbit_inliers.quantile(0.05), tolerance=5)
    else:
        rep.note('The inlier counts and fit errors of the finch specimens come from the full run; in a quick run the '
                 'comparisons with the finch dataset are skipped.')
    rep.check('Fits meeting both criteria (at least 40 inliers, fit error at most 10%)', '38', birds.ok.sum())
    rep.check('Flagged fits', '13', (~birds.ok).sum())

    coccinea = birds[birds.species == 'Vestiaria coccinea']
    rep.check('V. coccinea specimens', '4', len(coccinea))
    rep.check('V. coccinea: sphere centre, smallest position along the length (%)', '66',
              coccinea.sphere_center_along_pct.min())
    rep.check('V. coccinea: sphere centre, largest position along the length (%)', '74',
              coccinea.sphere_center_along_pct.max())
    rep.check('V. coccinea: fewest vertices', '19', coccinea.orbit_inliers.min())
    rep.check('V. coccinea: most vertices', '37', coccinea.orbit_inliers.max())
    if full:
        rep.check('Finch specimens: sphere centre, smallest position along the length (%)', '40',
                  finch.sphere_center_along_pct.min(), tolerance=1.0)
        rep.check('Finch specimens: sphere centre, largest position along the length (%)', '60',
                  finch.sphere_center_along_pct.max(), tolerance=1.0)
    flagged = birds[~birds.ok].copy()
    flagged['band_edge'] = [('band' in flag_reason(row)) for row in flagged.itertuples()]
    rep.check('Skulls flagged by a sphere centre within 5% of a band edge', '4', flagged.band_edge.sum())
    rep.check('... all of them V. coccinea', '4', (flagged.band_edge & (flagged.species == 'Vestiaria coccinea')).sum())
    others = flagged[~flagged.band_edge]
    rep.check('Of the remaining nine: fits on a small orbital patch', '4',
              (others.orbit_inliers < QUALITY['min_inliers']).sum())
    rep.check('... fewest vertices', '26', others.orbit_inliers[others.orbit_inliers < QUALITY['min_inliers']].min())
    rep.check('... most vertices', '36', others.orbit_inliers[others.orbit_inliers < QUALITY['min_inliers']].max())
    rep.check('Of the remaining nine: fit error above 10% of the radius', '5',
              (others.fit_error_pct > QUALITY['max_fit_error']).sum())
    if full:
        flagged_finches = ~reliable(finch)
        rep.check('The same criteria applied to the finch specimens: flagged fits', '7', flagged_finches.sum())
        rep.check('Spearman, sphere radius vs L, all 100 finch specimens', '0.854',
                  spearman(finch.sphere_radius, finch.L)[0])
        kept = finch[~flagged_finches]
        rep.check('Spearman, sphere radius vs L, excluding the flagged finch fits', '0.858',
                  spearman(kept.sphere_radius, kept.L)[0])

    rep.check('Spearman, sphere radius vs skull size L, reliable fits', '0.70', spearman(good.sphere_radius, good.L)[0])
    rep.check('Spearman, sphere radius vs L, finch specimens', '0.85', spearman(finch.sphere_radius, finch.L)[0])
    within = good.groupby('species').filter(lambda g: len(g) >= 3)
    variation = within.groupby('species').sphere_radius.agg(lambda r: 100 * r.std(ddof=1) / r.mean())
    rep.note('Coefficient of variation of the radius in the species with at least three reliable fits: '
             + ', '.join(f'{name} {value:.1f}%' for name, value in variation.items()) + '.')
    rep.check('Coefficient of variation of the radius within species (at least 3 specimens): smallest (%)', '5',
              variation.min(), tolerance=0.5)
    rep.check('Coefficient of variation within species: largest (%)', '15', variation.max(), tolerance=0.5)
    finch_species = ['genus', 'species'] if 'genus' in finch.columns else ['species']
    finch_variation = finch.groupby(finch_species).filter(lambda g: len(g) >= 3).groupby(
        finch_species).sphere_radius.agg(lambda r: 100 * r.std(ddof=1) / r.mean())
    rep.check('Finch species: median coefficient of variation (%)', '9', finch_variation.median(), tolerance=0.5)
    rep.check('Finch species: largest coefficient of variation (%)', '17', finch_variation.max(), tolerance=0.5)

    good = good.copy()
    good['predicted'] = MODEL_COEFFICIENTS[0] + (good[DIMS] * MODEL_COEFFICIENTS[1:]).sum(axis=1)
    good['relative'] = (good.predicted - good.curvature) / good.curvature
    cardueline, honeycreeper = good[good.group == CARD], good[good.group == HC]
    rep.note('Eq. (8) is applied with the coefficients as printed in the main text, as in SI Table S11.')
    rep.check('Cardueline relatives: mean relative error of Eq. (8) (%)', '9.7',
              100 * cardueline.relative.abs().mean())
    rep.check('Cardueline relatives: median relative error (%)', '4.7', 100 * cardueline.relative.abs().median())
    rep.check('Cardueline relatives: specimens below 10%', '7', (cardueline.relative.abs() < 0.10).sum())
    rep.check('Cardueline relatives: systematic bias (%)', '-0.7', 100 * cardueline.relative.mean())
    rep.check('Honeycreepers: reliable fits used', '29', len(honeycreeper))
    rep.check('Honeycreepers: mean relative error (%)', '12.0', 100 * honeycreeper.relative.abs().mean())
    rep.check('Honeycreepers: median relative error (%)', '10.0', 100 * honeycreeper.relative.abs().median())
    rep.check('Honeycreepers: under-prediction of the curvature (%)', '-8.3', 100 * honeycreeper.relative.mean())
    rep.check('Honeycreepers: specimens below 10%', '14', (honeycreeper.relative.abs() < 0.10).sum())
    rep.check('Honeycreepers: specimens below 20%', '25', (honeycreeper.relative.abs() < 0.20).sum())
    rep.check('Median radius / height z, reliable fits', '0.22', (good.sphere_radius / good.height_z).median())
    rep.check('Median radius / height z, finch specimens', '0.24', (finch.sphere_radius / finch.height_z).median())
    rep.check('Spearman, sphere radius vs L, honeycreepers', '0.67', spearman(honeycreeper.sphere_radius, honeycreeper.L)[0])
    for dim, printed in zip(DIMS, ['0.42', '0.66', '0.68']):
        rep.check(f'Spearman, sphere radius vs {dim}, honeycreepers', printed,
                  spearman(honeycreeper.sphere_radius, honeycreeper[dim])[0])
    for dim, printed in zip(DIMS, ['0.76', '0.84', '0.85']):
        rep.check(f'Spearman, sphere radius vs {dim}, finch specimens', printed,
                  spearman(finch.sphere_radius, finch[dim])[0])

    rodents = O[O.group == RODENT]
    rep.check('Rodent skulls', '2', len(rodents))
    rep.note('The fitted spheres in the two rodent examples do not identify the orbits, so no orbital measurements '
             'are reported for these specimens. Their orbital measurement cells are intentionally blank. '
             'The rodent skulls do not come from the remeshing of SI Section S1 and are oriented by their principal '
             'axes for the exploratory fit illustrations.')


def run_bilateral_statistics(D, O, full, rep):
    rep.section('SI Section S5: agreement between the two orbits')
    if not full:
        rep.note('SI Section S5 needs the fits; it is skipped in a quick run (QUICK_RUN = True).')
        return
    example = D[D.filename == 'G.DifficilisA.stl']
    if len(example):
        one = example.iloc[0]
        rep.check('SI Fig. S2(a), G. difficilis specimen A: fit error (%)', '3.7', one.fit_error_pct)
        rep.check('SI Fig. S2(b), G. difficilis specimen A: difference between the two radii (%)', '2.8',
                  100 * abs(one.second_sphere_radius - one.sphere_radius) / one.sphere_radius)

    for label, frame, printed in [('finch specimens', D, ['83', '5', '9', '0.86']),
                                  ('honeycreepers and relatives', O[(O.group != RODENT) &
                                                                    (~O.species.isin(ASYMMETRIC))],
                                   ['28', '6', '11', '0.79'])]:
        pair = frame[(frame.second_orbit_inliers >= QUALITY['min_inliers']) &
                     (frame.second_fit_error_pct <= QUALITY['max_fit_error'])]
        difference = 100 * (pair.second_sphere_radius - pair.sphere_radius).abs() / pair.sphere_radius
        rep.check(f'Second orbit meeting the criteria, {label}', printed[0], len(pair))
        # These statements describe coverage at fixed bounds, not interpolated quantiles.
        for threshold, minimum, fraction in [(printed[1], '>=50', 'half'),
                                              (printed[2], '>=75', 'three quarters')]:
            rep.check(f'{label}: at least {fraction} within {threshold}% between radii (coverage %)', minimum,
                      100 * (difference <= float(threshold)).mean())
        if label == 'finch specimens':
            rep.check('Finch specimens: at least nine tenths within 15% between radii (coverage %)', '>=90',
                      100 * (difference <= 15).mean())
        else:
            rep.check('Honeycreepers and relatives: specimens within 13% between radii', '25',
                      (difference <= 13).sum())
            remaining = difference[difference > 13]
            rep.check('Honeycreepers and relatives: remaining specimens', '3', len(remaining))
            rep.check('Remaining specimens: smallest difference between radii (%)', '23', remaining.min())
            rep.check('Remaining specimens: largest difference between radii (%)', '27', remaining.max())
        rep.check(f'Spearman between the two sides, {label}', printed[3],
                  spearman(pair.sphere_radius, pair.second_sphere_radius)[0])
    rep.check('Skulls of the other taxa used for the comparison (the asymmetric Loxops excluded)', '48',
              ((O.group != RODENT) & (~O.species.isin(ASYMMETRIC))).sum())
    rep.note('The second orbit is fitted with the search band restricted to the half of the skull that the first fit '
             'did not use; everything else is the fit of the paper. The difference between the two radii is taken '
             'relative to the radius of the first fit.')


def compare_with_dataset(M, dataset, rep):
    rep.section('SI Section S1: recomputed measurements against Dataset.xlsx')
    merged = M.merge(dataset, on='filename', suffixes=('', '_file'))
    groups = [('Bounding-box dimensions', DIMS, '<1e-5'), ('Sphere radius and centre',
              ['sphere_radius', 'sphere_center_x', 'sphere_center_y', 'sphere_center_z'], '<1e-5'),
              ('Ellipsoid semi-axes and centre', ['ellipsoid_axis_a', 'ellipsoid_axis_b', 'ellipsoid_axis_c',
                                                  'ellipsoid_center_x', 'ellipsoid_center_y', 'ellipsoid_center_z'], '<1e-6')]
    for label, columns, printed in groups:
        present = [c for c in columns if c + '_file' in merged.columns]
        if present:
            largest = np.nanmax(np.abs(merged[present].values - merged[[c + '_file' for c in present]].values))
            rep.check(f'{label}: largest difference to Dataset.xlsx (mm)', printed, largest)
    rep.check('Specimens with a fitted orbit sphere', '100', M.sphere_radius.notna().sum())
    rep.check('Specimens with a fitted braincase ellipsoid', '100', M.ellipsoid_axis_a.notna().sum())
    absent = [c for c in ('orbit_inliers', 'fit_error_pct') if c not in dataset.columns]
    if absent:
        rep.note('SI Section S4 states that the inlier count and the fit error of every finch specimen are given in '
                 'Dataset.xlsx, which does not contain ' + ' or '.join(absent) + '. Both are in the file '
                 'output/verify_all/measurements.xlsx written by this run; copy the columns into Dataset.xlsx before release.')


COMMON_NAMES = {'Camarhynchus': 'Tree Finch', 'Certhidea': 'Warbler Finch', 'Geospiza': 'Ground Finch',
                'Pinaroloxias': 'Cocos Finch', 'Platyspiza': 'Vegetarian Finch', 'Coereba': 'Bananaquit',
                'Euneornis': 'Orangequit', 'Loxigilla': 'Bullfinch', 'Loxipasser': 'Grassquit',
                'Melopyrrha': 'Cuban Bullfinch', 'Tiaris': 'Grassquit'}
GROUP_COLUMNS = [r"\textbf{Darwin's finches}", r'\textbf{DF relatives}', r'\textbf{All}']
DIMENSION_ROWS = [r'\textbf{Length $x$}', r'\textbf{Width $y$}', r'\textbf{Height $z$}']
REMESHING_NOTE = (r'The last column gives the value of the parameter used in the voxelization-based remeshing of each '
                  r'specimen (default 60; an asterisk marks the specimens for which the default was changed, see '
                  r'Materials and Methods of the main text).')
CAPTION_S7 = (r"Composition of the widest specimens in Fig.~9 of the main text. ``min'': smallest value among the "
              r"specimens beyond the gap, i.e., the five \textit{G.~magnirostris} in Darwin's finches and the ten "
              r"\textit{L.~violacea} and \textit{L.~portoricensis} in the relatives; ``others'': largest value among all "
              r"other specimens of the group ($n=48$ and $n=37$); ``gap'': their difference. All values in mm. The three "
              r"alternative width measures are defined in the text.")
CAPTION_S8 = (r"Spearman correlation between skull dimensions and 1/(orbit curvature) with all specimens (``all'', as in "
              r"Table~\ref{tab:spearman_1overr}) and without the specimens of \textit{G.~magnirostris}, "
              r"\textit{L.~violacea} and \textit{L.~portoricensis} (``without'').")
CAPTION_S9 = (r'Normalized orbit curvature $S/\hat{r}$ for different choices of the size variable $S$ (first row: '
              r'$\tilde{\kappa}$ of the main text). Spearman correlation of the ratio with the characteristic skull size '
              r'$L$ over all 100 specimens, and one-way ANOVA of the ratio across the eleven genera.')
CAPTION_S10 = (r'Genus means ($\pm$ SD) of the three size-independent descriptors of the main text and of the '
               r'characteristic skull size $L$.')
CAPTION_S11 = (r'Prediction of the orbit curvature from the skull dimensions with the three-predictor model of the main '
               r'text (first row) and with a single size variable (Eq.~(S1), rows 2--5). All models are least-squares '
               r'fits on the same 50 training specimens (dimensions in mm); $R^2_{\mathrm{test}}$ is the squared '
               r'correlation between predicted and measured curvature, Eq.~(S2), and MRE the mean relative error, '
               r'Eq.~(S3), both computed on the same 50 test specimens. The first row uses Eq.~(8) with the coefficients '
               r'as printed in the main text. The single-predictor equations in rows 2--5 are shown rounded to four '
               r'decimals; their $R^2_{\mathrm{test}}$ and MRE were computed with the full-precision fitted coefficients.')
NEUROCRANIUM_TABLES = [('S12', 'tab:pearson_various_df', 'Pearson', "Darwin's finches"),
                       ('S13', 'tab:spearman_various_df', 'Spearman', "Darwin's finches"),
                       ('S14', 'tab:pearson_various_dfr', 'Pearson', "the relatives of Darwin's finches"),
                       ('S15', 'tab:spearman_various_dfr', 'Spearman', "the relatives of Darwin's finches"),
                       ('S16', 'tab:pearson_various_both', 'Pearson', "both Darwin's finches and their relatives"),
                       ('S17', 'tab:spearman_various_both', 'Spearman', "both Darwin's finches and their relatives")]


def latex_escape(text):
    special = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{',
               '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}', '<': r'\textless{}',
               '>': r'\textgreater{}', '|': r'\textbar{}'}
    return ''.join(special.get(character, character) for character in str(text))


def _unwrap(text, command, before='', after=''):
    key = '\\' + command + '{'
    while key in text:
        start = text.index(key)
        depth, end = 1, start + len(key)
        while depth:
            depth += {'{': 1, '}': -1}.get(text[end], 0)
            end += 1
        text = text[:start] + before + text[start + len(key):end - 1] + after + text[end:]
    return text


SUPERSCRIPTS = str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹')


def to_plain(text):
    text = _unwrap(text, 'textcolor{red}', '**', '**')
    for old, new in [(r'\tilde{\kappa}', 'κ̃'), (r'\hat{r}', 'r̂'), (r'R^2_{\mathrm{test}}', 'R²_test'),
                     (r'F_{10,89}', 'F(10,89)'), (r'\eta^2', 'η²'), (r'\rho', 'ρ'), (r'\pm', '±'), ('^{1/3}', '^(1/3)'),
                     ('$^{*}$', '*'), (r'\,', ' '), (r'\%', '%'), ('``', '"'), ("''", '"'), ('--', '–'), ('~', ' ')]:
        text = text.replace(old, new)
    text = re.sub(r'\\times10\^\{(-?\d+)\}', lambda m: '×10' + m.group(1).translate(SUPERSCRIPTS), text)
    text = text.replace(r'Table \ref{tab:spearman_1overr}', 'Table S4')
    text = text.replace(r'\_', '_')
    for command in ('textbf', 'textit', 'mathrm', 'texttt'):
        text = _unwrap(text, command)
    return text.replace('$', '').strip()


def _cell(table, i, j, math=False):
    printed, value = table['reported'][i][j], table['values'][i][j]
    ok, text = agrees(printed, value)
    if ok is None:
        return '--', None
    exponent = re.fullmatch(r'(-?\d+(?:\.\d+)?)e([-+]\d+)', text)
    if exponent:
        text = rf'${exponent.group(1)}\times10^{{{int(exponent.group(2))}}}$'
    elif math:
        text = f'${text}$'
    return (text, None) if ok else (rf'\textcolor{{red}}{{{text}}}', f'{text} (printed {printed})')


def _pair(table, i, j_mean, j_sd):
    ok_mean, mean = agrees(table['reported'][i][j_mean], table['values'][i][j_mean])
    ok_sd, sd = agrees(table['reported'][i][j_sd], table['values'][i][j_sd])
    text = rf'${mean} \pm {sd}$'
    if ok_mean and ok_sd:
        return text, None
    printed = rf"${table['reported'][i][j_mean]} \pm {table['reported'][i][j_sd]}$"
    return rf'\textcolor{{red}}{{{text}}}', f'{text} (printed {printed})'


def build_si_tables(rep, specimens):
    models = {}

    def add(number, label, caption, header, body, spec, rules='booktabs', small=False, kind='results',
            differences=(), notes=()):
        models[number] = dict(number=number, label=label, caption=caption, header=header, body=body, spec=spec,
                              rules=rules, small=small, kind=kind, differences=list(differences), notes=list(notes))

    def matrix(number, rows, columns, math=False):
        body, differences = [], []
        for i, row in enumerate(rows):
            cells = []
            for j, column in enumerate(columns):
                text, note = _cell(rep.tables[number], i, j, math)
                cells.append(text)
                if note:
                    differences.append(f'{row} / {column}: {note}')
            body.append([row] + cells)
        return body, differences

    for number, label, group, who in [('S1', 'tab:DF_list', DF, "Darwin's finches"),
                                      ('S2', 'tab:DFR_list', REL, "relatives of Darwin's finches")]:
        body = [[str(r.specimen_id), rf'\textit{{{r.genus}}} ({COMMON_NAMES[r.genus]})', rf'\textit{{{r.species}}}',
                 f"{r.remeshing_parameter}{'$^{*}$' if r.remeshing_parameter != 60 else ''}"]
                for r in specimens[specimens.group == group].itertuples()]
        header = [[(r'\textbf{Specimen ID}', 1), (r'\textbf{Genus}', 1), (r'\textbf{Species}', 1),
                   (r'\textbf{Remeshing parameter}', 1)]]
        add(number, label, f'The list of specimens of {who} considered in our study. {REMESHING_NOTE}', header, body,
            '|c|c|c|c|', kind='specimens')

    for number, label, method, target, what in [
            ('S3', 'tab:pearson_1overr', 'Pearson correlation (Linear)', '1/(Orbit curvature)', '1/(orbit curvature)'),
            ('S4', 'tab:spearman_1overr', 'Spearman correlation (Monotonic)', '1/(Orbit curvature)', '1/(orbit curvature)'),
            ('S5', 'tab:pearson_r', 'Pearson correlation (Linear)', 'Orbit curvature', 'the orbit curvature'),
            ('S6', 'tab:spearman_r', 'Spearman correlation (Monotonic)', 'Orbit curvature', 'the orbit curvature')]:
        if number in rep.tables:
            body, differences = matrix(number, DIMENSION_ROWS, GROUP_COLUMNS)
            header = [[('', 1), (rf'\textbf{{{target}}} of', 3)], [('', 1)] + [(c, 1) for c in GROUP_COLUMNS]]
            add(number, label, f'{method} between skull dimensions and {what}.', header, body, 'lccc',
                differences=differences)

    if 'S7' in rep.tables:
        table = rep.tables['S7']
        rows = [('Bounding-box width y', r'\textbf{Bounding-box width $y$} (Fig.~9)'),
                ('99.5th-0.5th percentile width', r'\textbf{99.5th--0.5th percentile width}'),
                ('Width of the posterior quarter', r'\textbf{Width of the posterior quarter}'),
                ('Width after removing residual yaw', r'\textbf{Width after removing residual yaw}'),
                ('Bounding-box height z', r'\textbf{Bounding-box height $z$}'),
                ('Bounding-box length x', r'\textbf{Bounding-box length $x$}')]
        columns = [f'{group}, {name}' for group in ("Darwin's finches", 'DF relatives') for name in ('min', 'others', 'gap')]
        body, differences, notes = [], [], []
        for key, row in rows:
            if key not in table['rows']:
                body.append([row] + ['--'] * 6)
                notes = [r'Rows with -- are computed only in the full run (\texttt{QUICK\_RUN = False}).']
                continue
            i, cells = table['rows'].index(key), []
            for j, column in enumerate(columns):
                text, note = _cell(table, i, j)
                cells.append(text)
                if note:
                    differences.append(f'{row} / {column}: {note}')
            body.append([row] + cells)
        header = [[('', 1), (r"\textbf{Darwin's finches}", 3), (r'\textbf{DF relatives}', 3)],
                  [('', 1)] + [(name, 1) for name in ['min', 'others', 'gap'] * 2]]
        add('S7', 'tab:width_gap', CAPTION_S7, header, body, 'lcccccc', small=True, differences=differences, notes=notes)

    if 'S8' in rep.tables:
        columns = [f'{group}, {name}' for group in ("Darwin's finches", 'DF relatives', 'All') for name in ('all', 'without')]
        body, differences = matrix('S8', DIMENSION_ROWS, columns)
        header = [[('', 1), (r"\textbf{Darwin's finches}", 2), (r'\textbf{DF relatives}', 2), (r'\textbf{All}', 2)],
                  [('', 1)] + [(name, 1) for name in ['all', 'without'] * 3],
                  [('', 1)] + [(f'($n={n}$)', 1) for n in (53, 48, 47, 37, 100, 85)]]
        add('S8', 'tab:corr_without', CAPTION_S8, header, body, 'lcccccc', small=True, differences=differences)

    if 'S9' in rep.tables:
        table = rep.tables['S9']
        rows = [r'$L = (xyz)^{1/3}$ (main text, $\tilde{\kappa}$)', r'$x$ (length)', r'$y$ (width)', r'$z$ (height)',
                r'$(abc)^{1/3}$ (ellipsoid semi-axes)']
        columns = [r'Spearman $\rho$', r'Spearman $p$', r'ANOVA $F$', r'ANOVA $p$', r'$\eta^2$']
        body, differences = [], []
        for i, row in enumerate(rows):
            cells = []
            for j, column in enumerate(columns):
                text, note = _cell(table, i, j, math=(j == 0))
                cells.append(text)
                if note:
                    differences.append(f'{row} / {column}: {note}')
            body.append([row] + cells)
        header = [[(r'\textbf{Size variable $S$}', 1), (r'\textbf{Spearman with $L$}', 2),
                   (r'\textbf{One-way ANOVA across genera}', 3)],
                  [('', 1), (r'$\rho$', 1), (r'$p$', 1), (r'$F_{10,89}$', 1), (r'$p$', 1), (r'$\eta^2$', 1)]]
        add('S9', 'tab:alt_norm', CAPTION_S9, header, body, 'lccccc', small=True, differences=differences)

    if 'S10' in rep.tables:
        table = rep.tables['S10']
        columns = [r'$\tilde{\kappa} = L/\hat{r}$', r'$c/b$', r'$x/y$', r'$L$ (mm)']
        body, differences = [], []
        for i, genus in enumerate(GENERA):
            if i == 5:
                body.append('midrule')
            n_text, note = _cell(table, i, 0)
            if note:
                differences.append(rf'\textit{{{genus}}} / $n$: {note}')
            cells = [{0: "Darwin's finches", 5: 'DF relatives'}.get(i, ''), rf'\textit{{{genus}}}', n_text]
            for column, (j_mean, j_sd) in zip(columns, [(1, 2), (3, 4), (5, 6), (7, 8)]):
                text, note = _pair(table, i, j_mean, j_sd)
                cells.append(text)
                if note:
                    differences.append(rf'\textit{{{genus}}} / {column}: {note}')
            body.append(cells)
        header = [[('', 1), (r'\textbf{Genus}', 1), (r'$n$', 1)] + [(c, 1) for c in columns]]
        add('S10', 'tab:genus_descriptors', CAPTION_S10, header, body, 'llccccc', small=True, differences=differences)

    if 'S11' in rep.tables:
        table = rep.tables['S11']
        rows = [r'$x$, $y$, $z$ jointly', r'$L = (xyz)^{1/3}$', r'$z$ (height)', r'$y$ (width)', r'$x$ (length)']
        body, differences = [], []
        for i, (row, symbol) in enumerate(zip(rows, [None, 'L', 'z', 'y', 'x'])):
            if symbol is None:
                model = r'Eq.~(8) of the main text'
            else:
                def equation(intercept, slope):
                    return rf"${intercept} {'-' if slope.startswith('-') else '+'} {slope.lstrip('-')}\,{symbol}$"
                ok_0, intercept = agrees(table['reported'][i][0], table['values'][i][0])
                ok_1, slope = agrees(table['reported'][i][1], table['values'][i][1])
                model = equation(intercept, slope)
                if not (ok_0 and ok_1):
                    differences.append(f"{row} / fitted model: {model} (printed "
                                       f"{equation(table['reported'][i][0], table['reported'][i][1])})")
                    model = rf'\textcolor{{red}}{{{model}}}'
            cells = [row, model]
            for j, column in [(2, r'$R^2_{\mathrm{test}}$'), (3, 'MRE')]:
                text, note = _cell(table, i, j)
                cells.append(text)
                if note:
                    differences.append(f'{row} / {column}: {note}')
            body.append(cells)
        header = [[(r'\textbf{Predictor(s)}', 1), (r'\textbf{Fitted model (50 training specimens)}', 1),
                   (r'$R^2_{\mathrm{test}}$', 1), (r'\textbf{MRE (\%)}', 1)]]
        add('S11', 'tab:size_only', CAPTION_S11, header, body, 'llcc', small=True, differences=differences)

    rows = [r'\textbf{Ellipsoid semi-axis a}', r'\textbf{Ellipsoid semi-axis b}', r'\textbf{Ellipsoid semi-axis c}',
            r'\textbf{1/Curvature}', r'\textbf{Curvature}']
    columns = [r'\textbf{Length $x$}', r'\textbf{Width $y$}', r'\textbf{Height $z$}', r'\textbf{1/Curvature}',
               r'\textbf{Curvature}']
    for number, label, method, who in NEUROCRANIUM_TABLES:
        if number in rep.tables:
            body, differences = matrix(number, rows, columns)
            header = [[(r'\textbf{Variable}', 1)] + [(c, 1) for c in columns]]
            add(number, label, f'{method} correlation between various geometric quantities of {who}.', header, body,
                'lccccc', rules='hline', differences=differences)
    return models


def latex_table(model):
    top, middle, bottom = ((r'\toprule', r'\midrule', r'\bottomrule') if model['rules'] == 'booktabs'
                           else (r'\hline', r'\hline', r'\hline'))
    header = [' & '.join(text if span == 1 else rf'\multicolumn{{{span}}}{{c}}{{{text}}}' for text, span in row) + r' \\'
              for row in model['header']]
    body = [middle if row == 'midrule' else ' & '.join(row) + r' \\' for row in model['body']]
    if model['kind'] == 'specimens':
        environment = 'table'
        tabular = ([r'\resizebox{0.7\textwidth}{!}{', rf"\begin{{tabular}}{{{model['spec']}}}", r'\hline'] + header
                   + [r'\hline'] + body + [r'\hline', r'\end{tabular}', '}'])
    else:
        environment = 'table*'
        tabular = ([rf"\begin{{tabular*}}{{\textwidth}}{{@{{\extracolsep\fill}}{model['spec']}@{{\extracolsep\fill}}}}",
                    top] + header + [middle] + body + [bottom, r'\end{tabular*}'])
    lines = [rf'\setcounter{{table}}{{{int(model["number"][1:]) - 1}}}', rf'\begin{{{environment}}}[t]', r'\centering']
    lines += ([r'\small'] if model['small'] else []) + tabular
    remarks = list(model['notes'])
    if model['differences']:
        remarks.append(r'{\color{red}Differs from the printed table: ' + '; '.join(model['differences']) + '.}')
    if remarks:
        lines.append(r'\par\smallskip{\footnotesize ' + ' '.join(remarks) + r'\par}')
    lines += [rf"\caption{{{model['caption']}}}", rf"\label{{{model['label']}}}", rf'\end{{{environment}}}']
    return '\n'.join(lines)


def markdown_table(model):
    width = sum(span for _, span in model['header'][0])
    names = [''] * width
    for row in model['header']:
        position = 0
        for text, span in row:
            for k in range(span):
                piece = to_plain(text)
                if piece:
                    names[position + k] = f'{names[position + k]} {piece}'.strip()
            position += span
    lines = [f"**Table {model['number']}.** {to_plain(model['caption'])}", '',
             '| ' + ' | '.join(md(name) for name in names) + ' |', '|' + '---|' * width]
    lines += ['| ' + ' | '.join(md(to_plain(cell)) for cell in row) + ' |' for row in model['body'] if row != 'midrule']
    remarks = model['notes'] + (['Differs from the printed table: ' + '; '.join(to_plain(d) for d in model['differences']) + '.']
                                if model['differences'] else [])
    return lines + ([''] + remarks if remarks else [])


def _readable(text):
    text = latex_escape(text)
    for old, new in [(r'length\_x', r'length $x$'), (r'width\_y', r'width $y$'), (r'height\_z', r'height $z$'),
                     (r'R2\_test', r'$R^2_{\mathrm{test}}$'), (r'eta\textasciicircum{}2', r'$\eta^2$'),
                     (r'\textbar{}rho\textbar{}', r'$|\rho|$'), (' rho', r' $\rho$'), (r'\textless{}=', r'$\le$ '),
                     (r'\textless{}', r'$<$ ')]:
        text = text.replace(old, new)
    return text


def write_si_latex(models, rep, out, generated, mode, versions):
    checks = [item[1] for item in rep.items if item[0] == 'check']
    parts = [r'\documentclass[12pt]{article}', r'\usepackage[margin=1in]{geometry}',
             r'\usepackage{amsmath,amssymb,graphicx,xcolor,booktabs,longtable,array,caption}',
             r'\renewcommand{\thetable}{S\arabic{table}}', r'\begin{document}',
             r'\begin{center}{\LARGE\bfseries Reproduction of the numerical results}\\[1.2ex]'
             r'{\large Robust parametric estimation of avian cranial morphology}\\[0.6ex]'
             r'K. Lau and G. P. T. Choi\end{center}', r'\vspace{1em}']
    rows = pd.DataFrame(rep.rows())
    total, agree = len(rows), int((rows.agrees == 'yes').sum())
    message = verdict(rows.agrees.value_counts())
    colour, fill = ('green!45!black', 'green!7') if agree == total else ('red!60!black', 'red!5')
    parts += [r'\noindent\fcolorbox{' + colour + '}{' + fill + r'}{\parbox{\dimexpr\textwidth-2\fboxsep-2\fboxrule}'
              r'{\centering\rule{0pt}{4ex}\Large\textbf{' + message + r'}\rule[-2.2ex]{0pt}{0pt}}}\par', r'\vspace{1.2em}',
              r'\noindent The script \texttt{' + latex_escape(SCRIPT) + r'} fitted the orbit sphere and the neurocranium '
              r'ellipsoid to each of the 100 finch skull meshes of the repository, fitted the orbit of the skulls of SI '
              r'Section~S4, recomputed the statistics encoded from the main text '
              r'and the Supporting Information from these measurements, and compared each value with the value '
              r'printed in the paper. A value counts as reproduced when, rounded to the precision printed in the paper, '
              r'it equals the printed value. The tables of the Supporting Information follow, rebuilt from the '
              r'recomputed values, followed by the encoded comparisons with the text.',
              r'\section*{Summary}', r'\begin{tabular}{>{\raggedright\arraybackslash}p{0.66\textwidth}rr}', r'\toprule',
              r'\textbf{Part of the paper} & \textbf{Numbers} & \textbf{Reproduced} \\', r'\midrule']
    summary = rows.groupby('section', sort=False)['agrees'].agg(numbers='size', agree=lambda a: int((a == 'yes').sum()))
    parts += [latex_escape(section) + f' & {int(r.numbers)} & {int(r.agree)}' + r' \\' for section, r in summary.iterrows()]
    parts += [r'\midrule', rf'\textbf{{Total}} & \textbf{{{total}}} & \textbf{{{agree}}} \\', r'\bottomrule', r'\end{tabular}']
    differing = rows[rows.agrees != 'yes']
    if len(differing):
        parts += [r'\section*{Numbers that differ from the paper}', r'\begin{longtable}{>{\raggedright\arraybackslash}p{0.6\textwidth}cc}', r'\toprule',
                  r'\textbf{Quantity} & \textbf{Paper} & \textbf{Reproduced} \\', r'\midrule']
        parts += [_readable(r.quantity) + ' & ' + _readable(r.reported) + r' & \textcolor{red}{' + _readable(r.reproduced)
                  + r'} \\' for r in differing.itertuples()]
        parts += [r'\bottomrule', r'\end{longtable}']
    parts += [r'\vfill\noindent{\footnotesize Generated ' + latex_escape(generated) + '. Mode: ' + latex_escape(mode)
              + '. Software: ' + latex_escape(', '.join(versions)) + r'.\par}', r'\clearpage']
    for number in [f'S{k}' for k in range(1, 18)]:
        if number in models:
            parts.append(latex_table(models[number]))
            if number in ('S1', 'S2', 'S4', 'S6', 'S8', 'S10', 'S11', 'S13', 'S15', 'S17'):
                parts.append(r'\clearpage')
    parts += [r'\clearpage', r'\section*{Numbers stated in the text of the paper}',
              r'\begin{longtable}{>{\raggedright\arraybackslash}p{0.58\textwidth}ccc}', r'\toprule',
              r'\textbf{Quantity} & \textbf{Paper} & \textbf{Reproduced} & \textbf{Agrees} \\', r'\midrule', r'\endhead']
    section = None
    for row in checks:
        if row['section'] != section:
            section = row['section']
            parts.append(r'\multicolumn{4}{l}{\rule{0pt}{3ex}\textbf{' + latex_escape(section) + r'}} \\')
        agreement = r'\textcolor{red}{NO}' if row['agrees'] == 'NO' else latex_escape(row['agrees'])
        parts.append(' & '.join([_readable(row['quantity']), _readable(row['reported']),
                                 _readable(row['reproduced']), agreement]) + r' \\')
    parts += [r'\bottomrule', r'\end{longtable}', r'\end{document}']
    path = os.path.join(out, 'SI_tables.tex')
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write('\n'.join(parts) + '\n')
    return path


def compile_latex(tex_path):
    import glob
    import shutil
    candidates = [shutil.which('pdflatex'), '/Library/TeX/texbin/pdflatex', '/opt/homebrew/bin/pdflatex',
                  '/usr/local/bin/pdflatex', '/usr/bin/pdflatex'] + sorted(glob.glob('/usr/local/texlive/*/bin/*/pdflatex'))
    program = next((c for c in candidates if c and os.path.isfile(c)), None)
    if program is None:
        return None, 'no LaTeX found on this computer; compile SI_tables.tex with LaTeX or Overleaf'
    folder, name = os.path.split(tex_path)
    stem = tex_path[:-len('.tex')]
    for _ in range(2):
        try:
            result = subprocess.run([program, '-interaction=nonstopmode', '-halt-on-error', name], cwd=folder,
                                    capture_output=True, text=True, errors='replace', timeout=300)
        except (OSError, subprocess.TimeoutExpired) as error:
            return None, f'LaTeX could not run ({error})'
        if result.returncode != 0:
            return None, f'LaTeX stopped with an error; see {stem}.log'
    for extension in ('.aux', '.log', '.out'):
        if os.path.exists(stem + extension):
            os.remove(stem + extension)
    return stem + '.pdf', None


PAGE_STYLE = """
body { background: #f2f2ef; margin: 0; }
main { max-width: 900px; margin: 2rem auto; background: #fff; padding: 2.5rem 3rem; color: #111;
       font-family: "Latin Modern Roman", "CMU Serif", Georgia, "Times New Roman", serif; font-size: 16px;
       line-height: 1.45; box-shadow: 0 1px 4px rgba(0, 0, 0, .15); }
h1 { text-align: center; font-size: 1.9rem; margin: 0 0 .3rem; }
h2 { font-size: 1.35rem; margin-top: 2.4rem; }
.subtitle { text-align: center; margin: 0 0 1.5rem; }
.verdict { border: 2px solid; padding: 1rem; text-align: center; font-size: 1.4rem; font-weight: bold; margin: 1.5rem 0; }
.verdict.pass { border-color: #2e7d32; background: #eef8ee; }
.verdict.fail { border-color: #a32020; background: #fdf0f0; }
table { border-collapse: collapse; margin: 1.2rem auto .4rem; font-size: .92rem; }
th, td { padding: .2rem .7rem; text-align: center; vertical-align: top; }
th:first-child, td:first-child { text-align: left; }
table.booktabs { border-top: 2px solid #000; border-bottom: 2px solid #000; }
table.booktabs thead tr:last-child th { border-bottom: 1px solid #000; }
table.grid, table.grid th, table.grid td { border: 1px solid #000; text-align: center; }
tr.rule-above td { border-top: 1px solid #000; }
tr.group td { font-weight: bold; text-align: left; padding-top: .8rem; }
table.wide { width: 100%; }
.remarks { font-size: .85rem; text-align: center; margin: .3rem 0; }
.caption { font-size: .95rem; margin: .4rem 0 2.4rem; }
.differs { color: #c00000; }
.footer { font-size: .8rem; color: #555; margin-top: 2.5rem; }
@media print { body { background: #fff; } main { box-shadow: none; margin: 0; max-width: none; padding: 0; }
               section.table-block { page-break-inside: avoid; } }
"""


def to_html(text):
    text = html.escape(text, quote=False).replace(r'Table~\ref{tab:spearman_1overr}', 'Table S4')
    for old, new in [(r'\tilde{\kappa}', 'κ̃'), (r'\hat{r}', 'r̂'), (r'R^2_{\mathrm{test}}', 'R<sup>2</sup><sub>test</sub>'),
                     (r'F_{10,89}', 'F<sub>10,89</sub>'), (r'\eta^2', 'η<sup>2</sup>'), (r'\rho', 'ρ'), (r'\pm', '±'),
                     ('^{1/3}', '<sup>1/3</sup>'), ('$^{*}$', '<sup>*</sup>'), (r'\,', '&thinsp;'), (r'\%', '%'),
                     (r'\_', '_'), ('``', '“'), ("''", '”'), ('--', '–'), ('~', '&nbsp;')]:
        text = text.replace(old, new)
    text = re.sub(r'\\times10\^\{(-?\d+)\}', lambda m: '×10<sup>' + m.group(1).replace('-', '−') + '</sup>', text)
    text = _unwrap(text, 'textcolor{red}', '<span class="differs">', '</span>')
    for command, tag in (('textbf', 'b'), ('textit', 'i'), ('texttt', 'code')):
        text = _unwrap(text, command, f'<{tag}>', f'</{tag}>')
    text = _unwrap(text, 'mathrm')
    text = re.sub(r'\$([A-Za-z])\$', r'<i>\1</i>', text)
    return re.sub(r'\$([^$]*)\$', lambda m: m.group(1).replace('-', '−'), text)


def _readable_html(text):
    text = html.escape(str(text), quote=False)
    for old, new in [('length_x', 'length <i>x</i>'), ('width_y', 'width <i>y</i>'), ('height_z', 'height <i>z</i>'),
                     ('R2_test', 'R<sup>2</sup><sub>test</sub>'), ('eta^2', 'η<sup>2</sup>'), ('|rho|', '|ρ|'),
                     (' rho', ' ρ'), ('&lt;=', '≤ '), ('&lt;', '&lt; ')]:
        text = text.replace(old, new)
    return text


def html_table(model):
    lines = [f'<section class="table-block"><table class="{"grid" if model["kind"] == "specimens" else "booktabs"}">',
             '<thead>']
    for row in model['header']:
        lines.append('<tr>' + ''.join((f'<th colspan="{span}">' if span > 1 else '<th>') + to_html(text) + '</th>'
                                      for text, span in row) + '</tr>')
    lines.append('</thead><tbody>')
    rule_above = False
    for row in model['body']:
        if row == 'midrule':
            rule_above = True
            continue
        lines.append(('<tr class="rule-above">' if rule_above else '<tr>')
                     + ''.join(f'<td>{to_html(cell)}</td>' for cell in row) + '</tr>')
        rule_above = False
    lines.append('</tbody></table>')
    remarks = [to_html(note) for note in model['notes']]
    if model['differences']:
        remarks.append('<span class="differs">Differs from the printed table: '
                       + '; '.join(to_html(d) for d in model['differences']) + '.</span>')
    if remarks:
        lines.append('<p class="remarks">' + ' '.join(remarks) + '</p>')
    lines.append(f'<p class="caption">Table {model["number"]}: {to_html(model["caption"])}</p></section>')
    return '\n'.join(lines)


def write_si_html(models, rep, out, generated, mode, versions):
    rows = pd.DataFrame(rep.rows())
    total, agree = len(rows), int((rows.agrees == 'yes').sum())
    message = verdict(rows.agrees.value_counts())
    parts = ['<!DOCTYPE html>', '<html lang="en"><head><meta charset="utf-8">',
             '<title>Reproduction of the numerical results</title>', f'<style>{PAGE_STYLE}</style></head><body><main>',
             '<h1>Reproduction of the numerical results</h1>',
             '<p class="subtitle">Robust parametric estimation of avian cranial morphology<br>K. Lau and G. P. T. Choi</p>',
             f'<div class="verdict {"pass" if agree == total else "fail"}">{html.escape(message)}</div>',
             f'<p>The script <code>{html.escape(SCRIPT)}</code> fitted the orbit sphere and the neurocranium ellipsoid to '
             'each of the 100 finch skull meshes of the repository, fitted the orbit of the skulls of SI Section S4, '
             'recomputed the statistics encoded from the main text and the '
             'Supporting Information from these measurements, and compared each value with the value printed in the '
             'paper. A value counts as reproduced when, rounded to the precision printed in the paper, it equals the '
             'printed value. The tables of the Supporting Information follow, rebuilt from the recomputed values, and '
             'then the encoded comparisons with the text.</p>',
             '<h2>Summary</h2><table class="booktabs wide"><thead><tr><th>Part of the paper</th><th>Numbers</th>'
             '<th>Reproduced</th></tr></thead><tbody>']
    summary = rows.groupby('section', sort=False)['agrees'].agg(numbers='size', agree=lambda a: int((a == 'yes').sum()))
    parts += [f'<tr><td>{html.escape(section)}</td><td>{int(r.numbers)}</td><td>{int(r.agree)}</td></tr>'
              for section, r in summary.iterrows()]
    parts.append(f'<tr class="rule-above"><td><b>Total</b></td><td><b>{total}</b></td><td><b>{agree}</b></td></tr>'
                 '</tbody></table>')
    differing = rows[rows.agrees != 'yes']
    if len(differing):
        parts.append('<h2>Numbers that differ from the paper</h2><table class="booktabs wide"><thead><tr>'
                     '<th>Quantity</th><th>Paper</th><th>Reproduced</th></tr></thead><tbody>')
        parts += [f'<tr><td>{_readable_html(r.quantity)}</td><td>{_readable_html(r.reported)}</td>'
                  f'<td class="differs">{_readable_html(r.reproduced)}</td></tr>' for r in differing.itertuples()]
        parts.append('</tbody></table>')
    parts.append('<h2>Tables of the Supporting Information</h2>')
    parts += [html_table(models[number]) for number in [f'S{k}' for k in range(1, 18)] if number in models]
    parts.append('<h2>Numbers stated in the text of the paper</h2><table class="booktabs wide"><thead><tr>'
                 '<th>Quantity</th><th>Paper</th><th>Reproduced</th><th>Agrees</th></tr></thead><tbody>')
    section = None
    for item in rep.items:
        if item[0] != 'check':
            continue
        row = item[1]
        if row['section'] != section:
            section = row['section']
            parts.append(f'<tr class="group"><td colspan="4">{html.escape(section)}</td></tr>')
        agreement = '<span class="differs">NO</span>' if row['agrees'] == 'NO' else html.escape(row['agrees'])
        parts.append(f"<tr><td>{_readable_html(row['quantity'])}</td><td>{_readable_html(row['reported'])}</td>"
                     f"<td>{_readable_html(row['reproduced'])}</td><td>{agreement}</td></tr>")
    parts += ['</tbody></table>', f'<p class="footer">Generated {html.escape(generated)} by {html.escape(SCRIPT)}. '
              f'Mode: {html.escape(mode)}. Software: {html.escape(", ".join(versions))}.</p>', '</main></body></html>']
    path = os.path.join(out, 'SI_tables.html')
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write('\n'.join(parts) + '\n')
    return path


USE_COLOUR = (os.environ.get('PYCHARM_HOSTED') == '1' or sys.stdout.isatty()) and 'NO_COLOR' not in os.environ
if USE_COLOUR and os.name == 'nt':
    os.system('')


def _colour(text, code):
    return f'\x1b[{code}m{text}\x1b[0m' if USE_COLOUR else text


def _width(text):
    return sum(1 for character in re.sub(r'\x1b\[[0-9;]*m', '', text) if not unicodedata.combining(character))


def _fit(text, width, align):
    space = max(width - _width(text), 0)
    return text + ' ' * space if align == 'l' else ' ' * (space // 2) + text + ' ' * (space - space // 2)


def _wrap(text, width, code=None):
    lines = textwrap.wrap(text, width=width) or ['']
    return [_colour(line, code) if code else line for line in lines]


def console_text(text):
    return re.sub(r'\*\*(.+?)\*\*', lambda m: _colour(m.group(1), '31') if USE_COLOUR else m.group(1) + ' (!)',
                  to_plain(text))


def console_table(model, gap=3):
    align = re.findall(r'[lcr]', model['spec'])
    header = [[(console_text(text), span) for text, span in row] for row in model['header']]
    body = [row if row == 'midrule' else [console_text(cell) for cell in row] for row in model['body']]
    widths = [0] * len(align)
    for row in body:
        if row != 'midrule':
            for j, cell in enumerate(row):
                widths[j] = max(widths[j], _width(cell))
    for row in header:
        position = 0
        for text, span in row:
            if span == 1:
                widths[position] = max(widths[position], _width(text))
            position += span
    for row in header:
        position = 0
        for text, span in row:
            available = sum(widths[position:position + span]) + gap * (span - 1)
            if span > 1 and _width(text) > available:
                widths[position + span - 1] += _width(text) - available
            position += span
    total = sum(widths) + gap * (len(widths) - 1)
    text_width = min(max(total, 72), 110)
    lines = [_colour(f"Table {model['number']}", '1')] + _wrap(to_plain(model['caption']), text_width) + ['━' * total]
    for row in header:
        position, pieces = 0, []
        for text, span in row:
            pieces.append(_fit(text, sum(widths[position:position + span]) + gap * (span - 1),
                               align[position] if span == 1 else 'c'))
            position += span
        lines.append((' ' * gap).join(pieces).rstrip())
    lines.append('─' * total)
    for row in body:
        lines.append('─' * total if row == 'midrule' else
                     (' ' * gap).join(_fit(cell, widths[j], align[j]) for j, cell in enumerate(row)).rstrip())
    lines.append('━' * total)
    for note in model['notes']:
        lines += _wrap(to_plain(note), text_width)
    if model['differences']:
        lines += _wrap('Differs from the printed table: ' + '; '.join(to_plain(d) for d in model['differences']) + '.',
                       text_width, '31')
    return '\n'.join(lines)


def _readable_plain(text):
    for old, new in [('length_x', 'length x'), ('width_y', 'width y'), ('height_z', 'height z'), ('R2_test', 'R²_test'),
                     ('eta^2', 'η²'), ('|rho|', '|ρ|'), (' rho', ' ρ'), ('<=', '≤ ')]:
        text = str(text).replace(old, new)
    return text


def console_checks(rows, title, gap=3):
    widths = [min(70, max(_width(_readable_plain(r['quantity'])) for r in rows) + 2), 0, 0, 6]
    for r in rows:
        widths[1] = max(widths[1], _width(_readable_plain(r['reported'])), 5)
        widths[2] = max(widths[2], _width(_readable_plain(r['reproduced'])), 10)
    total = sum(widths) + gap * 3
    head = ['Quantity', 'Paper', 'Reproduced', 'Agrees']
    lines = [_colour(title, '1'), '━' * total,
             (' ' * gap).join(_fit(h, w, 'l' if k == 0 else 'c') for k, (h, w) in enumerate(zip(head, widths))), '─' * total]
    section = None
    for r in rows:
        if r['section'] != section:
            section = r['section']
            lines.append(_colour(section, '1'))
        quantity = _wrap(_readable_plain(r['quantity']), widths[0] - 2)
        agreement = _colour('NO', '31') if r['agrees'] == 'NO' else r['agrees']
        cells = [_readable_plain(r['reported']), _readable_plain(r['reproduced']), agreement]
        lines.append((' ' * gap).join([_fit('  ' + quantity[0], widths[0], 'l')]
                                      + [_fit(cell, w, 'c') for cell, w in zip(cells, widths[1:])]).rstrip())
        lines += ['  ' + line for line in quantity[1:]]
    lines.append('━' * total)
    return '\n'.join(lines)


def console_summary(rep):
    rows = pd.DataFrame(rep.rows())
    summary = rows.groupby('section', sort=False)['agrees'].agg(numbers='size', agree=lambda a: int((a == 'yes').sum()))
    width = max(len(section) for section in summary.index)
    total = width + 23
    lines = [_colour('Summary', '1'), '━' * total, f"{'Part of the paper':<{width}}   Numbers   Reproduced", '─' * total]
    lines += [f'{section:<{width}}   {int(r.numbers):>7}   {int(r.agree):>10}' for section, r in summary.iterrows()]
    lines += ['─' * total, f"{'Total':<{width}}   {len(rows):>7}   {int((rows.agrees == 'yes').sum()):>10}", '━' * total]
    return '\n'.join(lines)


def print_console_report(models, rep, everything):
    tables = [n for n in (f'S{k}' for k in range(1, 18)) if n in models and (everything or models[n]['differences'])]
    checks = [item[1] for item in rep.items if item[0] == 'check']
    checks = checks if everything else [row for row in checks if row['agrees'] != 'yes']
    if tables or checks:
        print()
    for number in tables:
        print(console_table(models[number]) + '\n')
    if checks:
        print(console_checks(checks, 'Numbers stated in the text of the paper' if everything else
                             'Numbers stated in the text that differ from the paper') + '\n')
    print(console_summary(rep))


def measure_all(meshes, specimens):
    rows = []
    for i, name in enumerate(specimens.filename, start=1):
        record, fits = measure_skull(os.path.join(meshes, name), extras=True, return_fits=True)
        rows.append(record)
        print(f"[{i:3d}/{len(specimens)}] {name:26s} orbit radius {record['sphere_radius']:.4f} mm, ellipsoid semi-axes "
              f"{record['ellipsoid_axis_a']:.2f}, {record['ellipsoid_axis_b']:.2f}, {record['ellipsoid_axis_c']:.2f} mm",
              flush=True)
        if SHOW_FITS is True or (isinstance(SHOW_FITS, (list, tuple, set)) and name in SHOW_FITS):
            title = f'{name} ({i}/{len(specimens)})'
            if fits['orbit'] is not None:
                show_orbit_fit(fits['mesh'], fits['orbit'], title)
            if fits['braincase'] is not None:
                show_braincase_fit(fits['mesh'], fits['braincase'], title)
    return pd.DataFrame(rows)


OTHER_COLUMNS = ['filename', 'group', 'species', 'length_x', 'width_y', 'height_z',
                 'orbit_patch', 'orbit_inliers', 'fit_error_pct', 'sphere_radius', 'curvature',
                 'sphere_center_x', 'sphere_center_y', 'sphere_center_z', 'sphere_center_along_pct',
                 'reliable', 'flag_reason', 'second_sphere_radius', 'second_orbit_inliers', 'second_fit_error_pct',
                 'closed', 'n_components', 'genus_largest']


def measure_other_taxa(folders, out):
    specimens = other_specimens(folders)
    rows = []
    for i, specimen in enumerate(specimens.itertuples(), start=1):
        record, fits = measure_other_skull(specimen.path, specimen.group)
        record.update(group=specimen.group, species=specimen.species,
                      remeshing_parameter=specimen.remeshing_parameter)
        rows.append(record)
        radius = record['sphere_radius']
        print(f'[{i:3d}/{len(specimens)}] {specimen.filename:30s} ' +
              ('no orbital measurement reported (exploratory rodent example)' if specimen.group == RODENT else
               f"orbit radius {radius:.4f} mm, {int(record['orbit_inliers'])} inliers, "
               f"fit error {record['fit_error_pct']:.1f}% of the radius" if np.isfinite(radius) else
               'no sphere accepted (no radius between 2 and 6 mm)'), flush=True)
        if SHOW_FITS is True or (isinstance(SHOW_FITS, (list, tuple, set)) and specimen.filename in SHOW_FITS):
            if fits['orbit'] is not None:
                show_orbit_fit(fits['mesh'], fits['orbit'], f'{specimen.filename} ({specimen.species})')
    O = pd.DataFrame(rows)
    O['curvature'] = 1.0 / O.sphere_radius
    O['reliable'] = np.where(O.group == RODENT, 'no fit reported', np.where(reliable(O), 'yes', 'flagged'))
    O['flag_reason'] = [flag_reason(row) if row.reliable == 'flagged' else '' for row in O.itertuples()]
    export_measurements(O[OTHER_COLUMNS]).to_excel(os.path.join(out, 'Dataset_other_taxa.xlsx'), index=False)
    return O


def find_repository(folder):
    root = os.path.abspath(folder or os.path.dirname(os.path.abspath(__file__)))
    meshes = locate_folder(root, FINCH_FOLDER_NAMES)
    spreadsheet = next((path for path in (os.path.join(root, 'Dataset.xlsx'),
                                          os.path.join(os.path.dirname(root), 'Dataset.xlsx'))
                        if os.path.isfile(path)), None)
    if spreadsheet is None or (meshes is None and not QUICK_RUN):
        missing = (['the folder of the 100 finch meshes (' + ' or '.join(FINCH_FOLDER_NAMES) + ')'] if meshes is None
                   else []) + (['the file Dataset.xlsx'] if spreadsheet is None else [])
        sys.exit(f'Cannot find {" and ".join(missing)} in {root}.\n'
                 'Put this file in the repository folder, or set REPOSITORY_FOLDER at the top of this file.')
    return root, meshes, spreadsheet


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    root, meshes, spreadsheet = find_repository(REPOSITORY_FOLDER)
    out = str(paths.output_dir(__file__))
    os.makedirs(os.path.join(out, 'tables'), exist_ok=True)
    dataset = pd.read_excel(spreadsheet, nrows=100)
    specimens = specimen_table(meshes if meshes else dataset.filename)
    other_folders = find_other_taxa(root) if OTHER_TAXA else []
    print(f'Repository folder: {root}')
    print(f'    {len(specimens)} finch meshes in {os.path.relpath(meshes, root)}/, measurements in '
          f'{os.path.relpath(spreadsheet, root)}' if meshes else
          f'    the 100 finch specimens of {os.path.relpath(spreadsheet, root)} (quick run; no mesh folder needed)')
    for folder, group, expected in other_folders:
        print(f'    {len(other_specimens([(folder, group, expected)]))} {group} meshes in '
              f'{os.path.relpath(folder, root)}/ (SI Section S4)')
    known = set(specimens.filename) | set(other_specimens(other_folders).filename)
    if isinstance(SHOW_FITS, (list, tuple, set)) and set(SHOW_FITS) - known:
        print('SHOW_FITS: no mesh named ' + ', '.join(sorted(set(SHOW_FITS) - known)) + ' in the folders above.')
    if SHOW_FITS and QUICK_RUN:
        print('SHOW_FITS has no effect in a quick run (QUICK_RUN = True), because no fits are made.')
    rep = Report(out)
    started = time.time()
    if QUICK_RUN:
        measured = dataset[['filename'] + DIMS + ['sphere_radius', 'ellipsoid_axis_a', 'ellipsoid_axis_b', 'ellipsoid_axis_c']]
        mode = 'quick (measurements read from Dataset.xlsx)'
    else:
        print('Fitting the orbit and the neurocranium of the 100 finch skull meshes (a few minutes).', flush=True)
        measured = measure_all(meshes, specimens)
        export_measurements(measured).to_csv(os.path.join(out, 'measurements.csv'), index=False)
        export_measurements(measured[COLUMNS]).to_excel(os.path.join(out, 'measurements.xlsx'), index=False)
        mode = 'full (all measurements recomputed from data/DF_and_their_relatives/*.stl)'
    print('Computing the statistics and comparing them with the paper.', flush=True)
    D = specimens.merge(measured.drop(columns=['curvature'], errors='ignore'), on='filename', validate='one_to_one').merge(
        dataset[['filename', 'Model']], on='filename', validate='one_to_one')
    run_statistics(D, specimens, not QUICK_RUN, rep)
    if not QUICK_RUN:
        compare_with_dataset(measured, dataset, rep)
    other = None
    if other_folders and not QUICK_RUN:
        missing = [f'{os.path.basename(folder)} ({len(other_specimens([(folder, group, expected)]))} of {expected} '
                   f'meshes)' for folder, group, expected in other_folders
                   if len(other_specimens([(folder, group, expected)])) != expected]
        if missing:
            print('Warning: ' + ', '.join(missing) + '. The numbers of SI Sections S4 and S5 will differ.')
        print(f'\nFitting the orbit of the {sum(len(other_specimens([f])) for f in other_folders)} skulls of '
              'SI Section S4 (a few minutes).', flush=True)
        other = measure_other_taxa(other_folders, out)
        globals()['MEASURED_MESHES'] = 100 + len(other)
    elif OTHER_TAXA and QUICK_RUN and os.path.isfile(os.path.join(root, 'Dataset_other_taxa.xlsx')):
        other = pd.read_excel(os.path.join(root, 'Dataset_other_taxa.xlsx'))
        print('Quick run: the measurements of SI Section S4 are read from Dataset_other_taxa.xlsx.')
    if other is not None:
        run_other_taxa_statistics(other, D, not QUICK_RUN, rep)
        run_bilateral_statistics(D, other, not QUICK_RUN, rep)
    elif OTHER_TAXA:
        rep.section('SI Sections S4 and S5: the skulls outside the finch dataset')
        rep.note('Not checked: the folders ' + ', '.join(names[0] for names, _, _ in OTHER_FOLDERS) + ' were not '
                 'found in the repository folder, in dataset_other_taxa/ or beside the repository folder. Put them in '
                 'one of those places, or set OTHER_TAXA = False to silence this.')
    versions = [f'Python {platform.python_version()}', f'NumPy {np.__version__}', f'SciPy {scipy.__version__}',
                f'trimesh {trimesh.__version__}', f'pandas {pd.__version__}', f'statsmodels {statsmodels.__version__}']
    header = ['# Reproduction of the numerical results', '',
              f"Generated {datetime.now():%Y-%m-%d %H:%M} in {time.time() - started:.0f} s by {SCRIPT}. "
              f"Mode: {mode}.", '', 'Software: ' + ', '.join(versions) + '.', '',
              'A number agrees when the reproduced value rounds to the value printed in the paper at the printed '
              'precision. In the tables, values in bold differ from the paper; the printed values are listed under '
              'each table.']
    models = build_si_tables(rep, specimens)
    counts = rep.write(header, models)
    print('Writing the SI tables in the layout of the Supporting Information.', flush=True)
    generated = f'{datetime.now():%Y-%m-%d %H:%M}'
    page = write_si_html(models, rep, out, generated, mode, versions)
    tex = write_si_latex(models, rep, out, generated, mode, versions)
    pdf, problem = compile_latex(tex)
    print_console_report(models, rep, everything=PRINT_TABLES)
    reproduced = counts.get('yes', 0) == sum(counts)
    print('\n' + _colour('Done. ' + verdict(counts) + ('' if reproduced else ' The details are shown above.'),
                         '1;32' if reproduced else '1;31'))
    if not reproduced:
        different = [f'{name} {installed_version(name)} (tested: {version})' for name, version in TESTED_VERSIONS.items()
                     if installed_version(name) != version]
        if different:
            print('Package versions differ from the tested ones: ' + ', '.join(different) + '. To rule this out, set '
                  'USE_TESTED_VERSIONS = True and run again.')
    print(f'The results are in {out}:')
    print('    SI_tables.html  the verdict, the SI tables in the layout of the Supporting Information, and the numbers '
          'of the text (opens in any web browser)')
    if pdf:
        print('    SI_tables.pdf   the same document as a PDF')
    else:
        print(f'    SI_tables.tex   the same document for LaTeX ({problem})')
    print('    report.md       encoded manuscript values next to the reproduced values')
    if other is not None and not QUICK_RUN:
        print('    Dataset_other_taxa.xlsx   the per-specimen values of SI Section S4 cited in the paper')
    if OPEN_RESULTS:
        try:
            webbrowser.open(Path(pdf or page).resolve().as_uri())
        except Exception:
            pass
    return 0 if reproduced else 1


if __name__ == '__main__':
    sys.exit(main())
