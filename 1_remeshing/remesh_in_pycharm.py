#!/usr/bin/env python3
"""Remesh raw skull surfaces with MATLAB; fitting is run separately in 2_fitting/."""
import argparse, glob, io, os, shutil, subprocess, sys, time
import pandas as pd

PARA_DEFAULT = 40
PARA = {
}
SEED       = 0
MESHFIX    = True
RESCALE    = False

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--raw', default=os.path.join(HERE, 'dataset_CT'))
ap.add_argument('--out', default=os.path.join(HERE, 'dataset_remeshed'))
ap.add_argument('--remeshing-dir', default=os.path.join(HERE, 'Remeshing'))
ap.add_argument('--params', default=os.path.join(HERE, 'params.csv'))
ap.add_argument('--matlab', default='matlab', help='matlab binary, used only if the engine is unavailable')
ap.add_argument('--once', action='store_true', help='process what is there now and exit instead of watching')
ap.add_argument('--overwrite', action='store_true', help='redo skulls whose remeshed STL already exists')
# Accepted for existing launch commands; remeshing does not open fitting windows.
ap.add_argument('--no-show', action='store_true', help=argparse.SUPPRESS)
a = ap.parse_args()

MESH_EXT = ('.stl', '.ply', '.obj', '.off')
def meshes(folder): return sorted(f for f in glob.glob(os.path.join(folder, '*')) if f.lower().endswith(MESH_EXT))
def stl_name(f): return os.path.splitext(os.path.basename(f))[0] + '.stl'
def current_para(raw_stl):
    if raw_stl in PARA: return int(PARA[raw_stl])
    if os.path.isfile(a.params):
        P = pd.read_csv(a.params, dtype={'filename': str})
        for r in P.itertuples():
            if str(r.filename).strip() == raw_stl: return int(r.para)
    return PARA_DEFAULT

def write_params_csv():
    rows = {}
    if os.path.isfile(a.params):
        for r in pd.read_csv(a.params, dtype={'filename': str}).itertuples(): rows[str(r.filename).strip()] = (int(r.para), getattr(r, 'reason', ''))
    for k, v in PARA.items(): rows[k] = (int(v), 'set in remesh_in_pycharm.py')
    for f in meshes(a.raw):
        rows.setdefault(stl_name(f), (PARA_DEFAULT, 'default'))
    p = os.path.join(a.out, '_params_effective.csv')
    pd.DataFrame([dict(filename=k, para=v[0], reason=v[1]) for k, v in rows.items()]).to_csv(p, index=False)
    return p

for d in (a.raw, a.out, os.path.join(a.out, '_stl_input')): os.makedirs(d, exist_ok=True)
def find_remeshing_dir(given):
    cands = [given, os.path.join(HERE, 'Remeshing'), os.path.expanduser('~/Documents/MATLAB/Remeshing')]
    for c in cands:
        if os.path.isfile(os.path.join(c, 'remesh_batch.m')) and os.path.isdir(os.path.join(c, 'code')): return c
    for root in (os.path.expanduser('~/Documents/MATLAB'), os.path.expanduser('~')):
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.count(os.sep) - root.count(os.sep) > 4: dirnames[:] = []; continue
            dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ('Library', 'node_modules', '.venv')]
            if 'remesh_batch.m' in filenames and 'code' in dirnames: return dirpath
    return None
found = find_remeshing_dir(a.remeshing_dir)
if found is None:
    sys.exit('remesh_batch.m was not found. Keep 1_remeshing/Remeshing/ with this repository, '
             'or pass --remeshing-dir with the folder containing remesh_batch.m and code/.')
a.remeshing_dir = found
print(f'MATLAB remeshing folder: {a.remeshing_dir}')

eng = None
try:
    import matlab.engine
    print('starting MATLAB engine ...', end=' ', flush=True); t0 = time.time()
    eng = matlab.engine.start_matlab()
    eng.addpath(eng.genpath(a.remeshing_dir), nargout=0)
    print(f'ready ({time.time()-t0:.0f} s)')
except Exception as e:
    print(f'MATLAB engine not available ({e.__class__.__name__}); will call the matlab binary "{a.matlab}" instead')

def remesh(stl_dir):
    params = write_params_csv()
    ov = bool(a.overwrite)
    if eng is not None:
        out = io.StringIO()
        eng.remesh_batch(stl_dir, a.out, params, 'Overwrite', ov, 'MeshFix', bool(MESHFIX), 'Rescale', bool(RESCALE),
                         'Seed', float(SEED), nargout=0, stdout=out, stderr=out)
        print(out.getvalue().strip())
    else:
        cmd = (f"addpath(genpath('{a.remeshing_dir}')); remesh_batch('{stl_dir}','{a.out}','{params}',"
               f"'Overwrite',{str(ov).lower()},'MeshFix',{str(bool(MESHFIX)).lower()},"
               f"'Rescale',{str(bool(RESCALE)).lower()},'Seed',{int(SEED)}); exit;")
        exe = a.matlab
        if shutil.which(exe) is None and not os.path.isfile(exe):
            apps = sorted(glob.glob('/Applications/MATLAB_R20*.app/bin/matlab'))
            if apps: exe = apps[-1]
            else: sys.exit('MATLAB binary not found. Give --matlab /Applications/MATLAB_R2025a.app/bin/matlab (your version)')
        r = subprocess.run([exe, '-batch', cmd])
        if r.returncode != 0:
            raise RuntimeError(f'MATLAB remeshing failed (exit status {r.returncode})')

def output_signature(path):
    if not os.path.isfile(path): return None
    stat = os.stat(path)
    return stat.st_size, stat.st_mtime_ns

def process_once():
    stl_dir = os.path.join(a.out, '_stl_input')
    todo = []
    for f in meshes(a.raw):
        rn = stl_name(f); target = os.path.join(a.out, f'{rn[:-4]}_p{current_para(rn)}.stl')
        if os.path.exists(target) and not a.overwrite: continue
        dst = os.path.join(stl_dir, rn)
        if f.lower().endswith('.stl'): shutil.copy(f, dst)
        else:
            import trimesh; trimesh.load_mesh(f, force='mesh').export(dst)
        todo.append(os.path.basename(target))
    if todo:
        print(f'\n=== remeshing {len(todo)} skull(s): {", ".join(todo)} ===')
        previous = {n: output_signature(os.path.join(a.out, n)) for n in todo}
        remesh(stl_dir)
        failed = []
        for n in todo:
            signature = output_signature(os.path.join(a.out, n))
            if signature is None or signature[0] == 0:
                failed.append(f'{n}: not produced or empty')
            elif a.overwrite and signature == previous[n]:
                failed.append(f'{n}: existing output was not updated')
        if failed:
            raise RuntimeError('; '.join(failed) + f' - see {os.path.join(a.out, "remeshing_log.csv")}')
    return len(todo)

try:
    n = process_once()
    if a.once:
        if n == 0: print(f'nothing new to remesh in {a.raw}')
    else:
        print(f'\nwatching {a.raw} - remeshed STL files appear in {a.out}; stop with Ctrl-C')
        while True:
            time.sleep(3)
            process_once()
except KeyboardInterrupt:
    print('stopped')
except RuntimeError as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
finally:
    if eng is not None: eng.quit()
