#!/usr/bin/env python3
import argparse, glob, math, os, re, sys
from pathlib import Path
import numpy as np, pandas as pd, trimesh
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from measurement_exports import export_measurements, is_rodent_filename


def sphere_loss(params, points):
    c, r = params[:3], params[3]
    if r <= 0:
        return 1e9
    return np.sum((np.linalg.norm(points - c, axis=1) - r) ** 2)


def fit_sphere_iteratively(points, max_iterations=3, outlier_std_dev=2.0):
    cur = points.copy()
    for _ in range(max_iterations):
        if len(cur) < 4:
            return None, None, cur
        c0 = cur.mean(axis=0)
        r0 = np.mean(np.linalg.norm(cur - c0, axis=1))
        res = minimize(sphere_loss, np.append(c0, r0), args=(cur,), method='L-BFGS-B',
                       bounds=[(None, None)] * 3 + [(1e-6, None)])
        c, r = res.x[:3], res.x[3]
        err = np.abs(np.linalg.norm(cur - c, axis=1) - r)
        mask = err < err.mean() + outlier_std_dev * err.std()
        if mask.all():
            break
        cur = cur[mask]
    fin = minimize(sphere_loss, res.x, args=(cur,), method='L-BFGS-B',
                   bounds=[(None, None)] * 3 + [(1e-6, None)])
    return fin.x[:3], fin.x[3], cur


def split_name(name):
    match = re.match(r'^(.*)_p(\d+)\.stl$', name, flags=re.IGNORECASE)
    return match.group(1) if match else name[:-4]


def accept(rule, r, L, rms, c, ext, rmin=2.0, rmax=6.0):
    if rule == 'mm':
        return rmin < r < rmax
    return (0.10 <= r / L <= 0.27) and (rms / r <= 0.25) and (abs(c[1]) <= ext[1] / 2)


def render(m, c, r, inl, seed_vertex, name, title, out_png):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    V, F = m.vertices, m.faces
    fig = plt.figure(figsize=(15, 9)); fig.suptitle(f'{name}   {title}', fontsize=10)
    gs = fig.add_gridspec(2, 3, height_ratios=[1.3, 1])
    views = [('left lateral (from -y)', (0, -90)), ('dorsal (from +z)', (90, -90)), ('right lateral (from +y)', (0, 90))]
    for i, (lab, (el, az)) in enumerate(views):
        ax = fig.add_subplot(gs[0, i], projection='3d'); ax.set_proj_type('ortho')
        ax.add_collection3d(Poly3DCollection(V[F], facecolor=(0.85, 0.85, 0.85, 0.35), edgecolor='none'))
        if inl is not None: ax.scatter(*inl.T, s=3, c='red', depthshade=False)
        ax.scatter(*V[seed_vertex], s=40, c='lime', depthshade=False)
        if c is not None:
            u, v = np.mgrid[0:2*np.pi:24j, 0:np.pi:12j]
            ax.plot_wireframe(c[0] + r*np.cos(u)*np.sin(v), c[1] + r*np.sin(u)*np.sin(v), c[2] + r*np.cos(v), color='blue', linewidth=0.4)
        lo, hi = V.min(0), V.max(0)
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2]); ax.set_box_aspect(hi - lo, zoom=1.25)
        ax.view_init(elev=el, azim=az); ax.set_axis_off(); ax.set_title(lab, fontsize=9)
    secs = [('coronal section (plane x = centre)', [1, 0, 0], (1, 2)), ('horizontal section (plane z = centre)', [0, 0, 1], (0, 1))]
    for j, (lab, normal, (ia, ib)) in enumerate(secs):
        ax = fig.add_subplot(gs[1, j])
        if c is not None:
            sec = m.section(plane_origin=c, plane_normal=normal)
            if sec is not None:
                for ent in sec.entities:
                    pts = sec.vertices[ent.points]; ax.plot(pts[:, ia], pts[:, ib], 'k-', linewidth=0.8)
            t = np.linspace(0, 2*np.pi, 200); ax.plot(c[ia] + r*np.cos(t), c[ib] + r*np.sin(t), 'b-', linewidth=1.2)
            ax.plot(c[ia], c[ib], 'b+', markersize=8)
            if inl is not None: ax.scatter(inl[:, ia], inl[:, ib], s=4, c='red', alpha=0.4)
        ax.set_aspect('equal'); ax.set_title(lab, fontsize=9); ax.tick_params(labelsize=7)
    ax = fig.add_subplot(gs[1, 2]); ax.axis('off')
    ax.text(0, 0.95, 'blue = fitted sphere\nred  = points used for the fit\ngreen = seed vertex\n\n'
                     'Sections: black = mesh outline through\nthe sphere centre; blue = fitted sphere.\n\n'
                     'Good orbit fit: circle on the concave bowl\nin at least one section; red points stay\n'
                     'inside the orbit; RMS/r < ~0.10\n(finch median 0.054, 95th pct 0.089).\n\n'
                     'Flattened orbit / large flat facets in the\nmesh = remeshing defect -> change para\nin params.csv and re-run with --overwrite.',
            fontsize=9, va='top', family='monospace')
    fig.subplots_adjust(left=0.03, right=0.99, top=0.93, bottom=0.05, wspace=0.05, hspace=0.15); fig.savefig(out_png, dpi=110); plt.close(fig)


def show_interactive(m, c, r, inl, seed_vertex, name, title, slices=True):
    import pyvista as pv
    faces = np.hstack([np.full((len(m.faces), 1), 3), m.faces]).astype(np.int64).ravel()
    pm = pv.PolyData(np.asarray(m.vertices, float), faces)
    plotter = pv.Plotter(title=name)
    plotter.add_text(f"{name}\n{title}", position='upper_left', font_size=11, color='black')
    plotter.add_mesh(pm, style='surface', opacity=0.4, color='lightgrey')
    if c is not None:
        plotter.add_mesh(pv.Sphere(radius=r, center=c), style='wireframe', color='blue', line_width=2)
        if inl is not None:
            plotter.add_points(np.asarray(inl, float), color='crimson', point_size=6, render_points_as_spheres=True, label='Selected Points (Inliers)')
        if slices:
            for normal in ('x', 'z'):
                try:
                    sl = pm.slice(normal=normal, origin=c)
                    if sl.n_points: plotter.add_mesh(sl, color='black', line_width=2)
                except Exception: pass
    plotter.add_points(np.asarray(m.vertices[seed_vertex], float)[None, :], color='lime', point_size=15, render_points_as_spheres=True, label='Seed Point')
    plotter.add_legend()
    plotter.show()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder'); ap.add_argument('out_prefix')
    ap.add_argument('--rule', choices=['mm', 'relative'], default='mm')
    ap.add_argument('--target', type=int, default=400)
    ap.add_argument('--ball', type=float, default=2.0)
    ap.add_argument('--roi', type=float, nargs=2, default=[0.30, 0.70])
    ap.add_argument('--rmin', type=float, default=2.0, help='lower radius bound in mm for the mm rule')
    ap.add_argument('--rmax', type=float, default=6.0, help='upper radius bound in mm for the mm rule')
    ap.add_argument('--seeds', type=int, default=15)
    ap.add_argument('--files', nargs='*', default=None, help='only these filenames (default: all *.stl in folder)')
    ap.add_argument('--render', default=None, help='folder for one PNG per skull (3 views + 2 sections)')
    ap.add_argument('--interactive', action='store_true', help='open the pyvista window for each skull (as in fit_sphere.py)')
    ap.add_argument('--no-slices', action='store_true', help='interactive window without the section outlines')
    a = ap.parse_args()
    if not (0 <= a.roi[0] < a.roi[1] <= 1):
        ap.error('--roi must satisfy 0 <= start < end <= 1')
    if not (math.isfinite(a.rmin) and math.isfinite(a.rmax) and 0 < a.rmin < a.rmax):
        ap.error('--rmin and --rmax must be finite and satisfy 0 < rmin < rmax')
    if a.render: os.makedirs(a.render, exist_ok=True)

    accepted, attempts, failed = [], [], []
    paths = sorted(glob.glob(os.path.join(a.folder, '*.stl')))
    if a.files: paths = [p for p in paths if os.path.basename(p) in set(a.files)]
    for fp in paths:
        name = os.path.basename(fp)
        specimen = split_name(name)
        rodent = is_rodent_filename(name)
        first_fit = None
        m = trimesh.load_mesh(fp)
        comps = m.split(only_watertight=False)
        if len(comps) > 1:
            m = sorted(comps, key=lambda c: len(c.vertices), reverse=True)[0]
        m.process(validate=True)
        ext = m.bounding_box.extents; b = m.bounds
        L = float(np.prod(ext) ** (1 / 3))
        roi = (m.vertices[:, 0] > b[0, 0] + ext[0] * a.roi[0]) & (m.vertices[:, 0] < b[0, 0] + ext[0] * a.roi[1])
        H = trimesh.curvature.discrete_mean_curvature_measure(m, m.vertices, radius=a.ball)
        Hroi = H.copy(); Hroi[~roi] = 1.0
        seeds = np.argsort(Hroi)[:a.seeds]
        init = np.zeros(len(m.vertices), bool); init[np.argsort(H)[:a.target]] = True
        valid = init & roi
        sel = m.edges[valid[m.edges].all(axis=1)]
        comps = trimesh.graph.connected_components(sel) if len(sel) else []

        ok = False; log = []
        for att, s in enumerate(seeds):
            row = dict(filename=name, specimen=specimen, attempt=att + 1, seed_vertex=int(s), L=L, width_y=ext[1])
            if not valid[s]:
                row['status'] = 'seed-invalid'; attempts.append(row); log.append(f'a{att+1}:seed-invalid'); continue
            idx = np.array([])
            for comp in comps:
                if s in comp:
                    idx = np.array(comp); break
            if len(idx) == 0 and comps:
                idx = np.array(max(comps, key=len))
            if len(idx) < 20:
                row.update(status='component<20', n_candidates=len(idx)); attempts.append(row)
                log.append(f'a{att+1}:{len(idx)}pts'); continue
            c, r, inl = fit_sphere_iteratively(m.vertices[idx])
            if c is None:
                row['status'] = 'fit-failed'; attempts.append(row); log.append(f'a{att+1}:fitfail'); continue
            rms = float(np.sqrt(np.mean((np.linalg.norm(inl - c, axis=1) - r) ** 2)))
            passed = accept(a.rule, r, L, rms, c, ext, a.rmin, a.rmax)
            if first_fit is None: first_fit = (c, r, inl, int(s), att + 1, rms)
            row.update(status='accepted' if passed else 'rejected', n_candidates=len(idx), n_inliers=len(inl),
                       sphere_radius=r, r_over_L=r / L, rms_residual_mm=rms, rms_over_radius=rms / r,
                       abs_cy_over_halfwidth=abs(c[1]) / (ext[1] / 2), cx=c[0], cy=c[1], cz=c[2])
            attempts.append(row)
            if not passed:
                log.append(f'a{att+1}:r={r:.2f},r/L={r/L:.3f},rms/r={rms/r:.3f},cy/hw={abs(c[1])/(ext[1]/2):.2f}'); continue
            accepted.append(dict(filename=name, specimen=specimen, length_x=ext[0], width_y=ext[1], height_z=ext[2], L=L,
                                 sphere_radius=r, sphere_center_x=c[0], sphere_center_y=c[1], sphere_center_z=c[2],
                                 curvature=1 / r, r_over_L=r / L, kappa_tilde=L / r, seed_attempt=att + 1,
                                 n_candidates=len(idx), n_inliers=len(inl), rms_residual_mm=rms,
                                 rms_over_radius=rms / r, abs_cy_over_halfwidth=abs(c[1]) / (ext[1] / 2),
                                 fit_side='y<0' if c[1] < 0 else 'y>0', rejected_attempts=';'.join(log)))
            ok = True; break
        if not ok:
            failed.append(f'{name}\t' + ('no orbital measurements; diagnostic fit only' if rodent else ';'.join(log)))
        if ok:
            acc = accepted[-1]
            fit_title = ("DIAGNOSTIC FIT ONLY - no orbital measurements" if rodent else
                         f"ACCEPTED seed {acc['seed_attempt']}  r={acc['sphere_radius']:.2f} mm  r/L={acc['r_over_L']:.3f}  "
                         f"inliers={acc['n_inliers']}  RMS/r={acc['rms_over_radius']:.3f}")
            render_center = np.array([acc['sphere_center_x'], acc['sphere_center_y'], acc['sphere_center_z']])
            render_radius, render_inliers, render_seed = acc['sphere_radius'], inl, int(s)
            render_suffix = '.png'
        elif first_fit is not None:
            render_center, render_radius, render_inliers, render_seed, att, rms = first_fit
            fit_title = ("DIAGNOSTIC FIT ONLY - no orbital measurements" if rodent else
                         f"FAILED - showing attempt {att}: r={render_radius:.2f} mm  r/L={render_radius/L:.3f}  "
                         f"inliers={len(render_inliers)}  RMS/r={rms/render_radius:.3f}")
            render_suffix = '_FAILED.png'
        else:
            render_center, render_radius, render_inliers, render_seed = None, None, None, int(seeds[0])
            fit_title = ("NO ORBITAL MEASUREMENTS - no diagnostic fit" if rodent else
                         'FAILED - no attempt produced a fit (components < 20 points)')
            render_suffix = '_FAILED.png'
        if a.interactive:
            show_interactive(m, render_center, render_radius, render_inliers, render_seed, name, fit_title,
                             slices=not a.no_slices and render_center is not None)
        if a.render:
            render(m, render_center, render_radius, render_inliers, render_seed, name, fit_title,
                   os.path.join(a.render, name[:-4] + render_suffix))
        if rodent:
            print(f'{name}: no orbital measurements; diagnostic fit only')
        else:
            print(f'{name}: ' + ('accepted at seed %d, r=%.3f' % (accepted[-1]['seed_attempt'], accepted[-1]['sphere_radius']) if ok else 'FAILED'))

    export_measurements(pd.DataFrame(accepted)).to_excel(a.out_prefix + '_accepted.xlsx', index=False)
    export_measurements(pd.DataFrame(attempts)).to_csv(a.out_prefix + '_attempts.csv', index=False)
    with open(a.out_prefix + '_failed.txt', 'w') as f:
        f.write('\n'.join(failed))
    n_accepted = sum(not is_rodent_filename(row['filename']) for row in accepted)
    n_failed = sum(not is_rodent_filename(line.split('\t')[0]) for line in failed)
    n_rodents = sum(is_rodent_filename(os.path.basename(path)) for path in paths)
    print(f'\nrule={a.rule} target={a.target} ball={a.ball} roi={a.roi}: '
          f'accepted {n_accepted}, failed {n_failed}, without orbital measurements {n_rodents}')


if __name__ == '__main__':
    main()
