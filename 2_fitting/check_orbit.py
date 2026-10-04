#!/usr/bin/env python3
import argparse, glob, math, os, platform, subprocess, sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from measurement_exports import export_measurements, is_rodent_filename

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--folder', default=os.path.join(HERE, '..', '1_remeshing', 'dataset_remeshed'))
ap.add_argument('--results', default=os.path.join(HERE, 'output', 'check_orbit'))
ap.add_argument('--all', action='store_true', help='re-fit every file, not only new ones')
ap.add_argument('--no-show', action='store_true')
ap.add_argument('--rule', default='relative'); ap.add_argument('--target', default='400'); ap.add_argument('--ball', default='2.0')
ap.add_argument('--roi', type=float, nargs=2, default=[0.30, 0.70])
ap.add_argument('--rmin', type=float, default=2.0, help='lower radius bound in mm for the mm rule')
ap.add_argument('--rmax', type=float, default=6.0, help='upper radius bound in mm for the mm rule')
ap.add_argument('--view', default='png', choices=['png', 'window', 'both'], help='png: save+open picture; window: interactive pyvista window')
a = ap.parse_args()
if not (0 <= a.roi[0] < a.roi[1] <= 1):
    ap.error('--roi must satisfy 0 <= start < end <= 1')
if not (math.isfinite(a.rmin) and math.isfinite(a.rmax) and 0 < a.rmin < a.rmax):
    ap.error('--rmin and --rmax must be finite and satisfy 0 < rmin < rmax')

fit_script = os.path.join(HERE, 'fit_sphere_logged.py')
render_dir = os.path.join(a.results, 'renders'); os.makedirs(render_dir, exist_ok=True)
prefix = os.path.join(a.results, '')
P = lambda ext: os.path.join(a.results, ext)

files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(a.folder, '*.stl')))
if not files: sys.exit(f'no .stl files in {a.folder}')
done = set()
if not a.all:
    if os.path.exists(P('accepted.xlsx')): done |= set(pd.read_excel(P('accepted.xlsx')).filename)
    if os.path.exists(P('failed.txt')): done |= {l.split('\t')[0] for l in open(P('failed.txt')).read().splitlines() if l.strip()}
todo = [f for f in files if f not in done]
if not todo: sys.exit('nothing new to fit (use --all to re-fit everything)')

run = os.path.join(a.results, '_run')
fit_cmd = [sys.executable, fit_script, a.folder, run, '--rule', a.rule, '--target', a.target, '--ball', a.ball,
           '--roi', str(a.roi[0]), str(a.roi[1]), '--rmin', str(a.rmin), '--rmax', str(a.rmax),
           '--render', render_dir, '--files', *todo]
if not a.no_show and a.view in ('window', 'both'): fit_cmd.append('--interactive')
if a.view == 'window': a.no_show = True
r = subprocess.run(fit_cmd)
if r.returncode != 0: sys.exit('fitting failed')

for ext in ('accepted.xlsx', 'attempts.csv'):
    rd = pd.read_excel if ext.endswith('xlsx') else pd.read_csv
    new = rd(run + '_' + ext) if os.path.exists(run + '_' + ext) else pd.DataFrame()
    old = rd(P(ext)) if os.path.exists(P(ext)) else pd.DataFrame()
    if len(old): old = old[~old.filename.isin(todo)]
    both = export_measurements(pd.concat([old, new], ignore_index=True))
    (both.to_excel if ext.endswith('xlsx') else both.to_csv)(P(ext), index=False)
    if os.path.exists(run + '_' + ext): os.remove(run + '_' + ext)
old = [l for l in (open(P('failed.txt')).read().splitlines() if os.path.exists(P('failed.txt')) else []) if l.split('\t')[0] not in todo]
new = [l for l in (open(run + '_failed.txt').read().splitlines() if os.path.exists(run + '_failed.txt') else []) if l.strip()]
failures = [line.split('\t')[0] + '\tno orbital measurements; diagnostic fit only'
            if is_rodent_filename(line.split('\t')[0]) else line for line in old + new]
open(P('failed.txt'), 'w').write('\n'.join(failures) + ('\n' if failures else ''))
if os.path.exists(run + '_failed.txt'): os.remove(run + '_failed.txt')

acc = pd.read_excel(P('accepted.xlsx')) if os.path.exists(P('accepted.xlsx')) else pd.DataFrame()
failed = {l.split('\t')[0]: (l.split('\t')[1] if '\t' in l else '') for l in open(P('failed.txt')).read().splitlines() if l.strip()}
rows = []
for f in files:
    r_ = acc[acc.filename == f] if len(acc) else acc
    if len(r_): rows.append({**r_.iloc[0].to_dict(), 'status': 'accepted'})
    elif f in failed: rows.append({'filename': f, 'status': 'failed', 'rejected_attempts': failed[f]})
    else: rows.append({'filename': f, 'status': 'not fitted'})
fin = export_measurements(pd.DataFrame(rows))
cols = ['filename', 'specimen', 'status'] + [c for c in fin.columns if c not in ('filename', 'specimen', 'status')]
fin = fin[[c for c in cols if c in fin.columns]]
fin.to_excel(P('final.xlsx'), index=False)

print('\n--- this run ---')
pngs = []
for f in todo:
    row = acc[acc.filename == f] if len(acc) else acc
    if is_rodent_filename(f):
        png = os.path.join(render_dir, f[:-4] + ('.png' if len(row) else '_FAILED.png'))
        print(f'{f:32s} NO ORBITAL MEASUREMENTS (diagnostic fit only)')
    elif len(row):
        x = row.iloc[0]; png = os.path.join(render_dir, f[:-4] + '.png')
        verdict = 'looks fine' if x.rms_over_radius <= 0.10 else 'CHECK: high residual (points spilled or flattened orbit)'
        print(f"{f:32s} ACCEPTED  r={x.sphere_radius:.2f} mm  r/L={x.r_over_L:.3f}  inliers={int(x.n_inliers)}  RMS/r={x.rms_over_radius:.3f}  seed {int(x.seed_attempt)}   {verdict}")
    else:
        png = os.path.join(render_dir, f[:-4] + '_FAILED.png')
        print(f"{f:32s} FAILED    (see results/failed.txt for what each seed gave)")
    if os.path.exists(png): pngs.append(png); print(f"{'':32s} picture: {png}")
rodent_count = sum(is_rodent_filename(name) for name in files)
print(f"--- total so far: {(fin.status=='accepted').sum()} accepted, {(fin.status=='failed').sum()} failed, "
      f"{rodent_count} without orbital measurements of {len(fin)} files -> {P('final.xlsx')} ---")
if pngs and not a.no_show:
    opener = {'Darwin': ['open'], 'Windows': ['cmd', '/c', 'start', '']}.get(platform.system(), ['xdg-open'])
    for png in pngs:
        try: subprocess.Popen(opener + [png])
        except Exception: pass
