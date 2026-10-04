import sys, os, glob
import numpy as np
import pandas as pd
import trimesh
import matplotlib

np.seterr(all="ignore")

SHOW = False
matplotlib.use("TkAgg" if SHOW else "Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_fit import run

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paths
from measurement_exports import export_measurements

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = str(paths.DATA)
FOLDERS = ["DF_and_their_relatives", "Honeycreepers_watertight", "HC_Relatives_watertight", "Peromyscus"]
LABELS = {"DF_and_their_relatives": "darwins_finches_and_relatives",
          "Honeycreepers_watertight": "hawaiian_honeycreepers",
          "HC_Relatives_watertight": "cardueline_relatives",
          "Peromyscus": "peromyscus"}
FINCH_FOLDERS = "DF_and_their_relatives|dataset"
OUT_DIR = os.path.join(str(paths.output_dir(__file__)), "orbit_fit_check")
PREFIX = "orbit_fit_check"
OUTPUT = "png"
CSV = os.path.join(str(paths.output_dir(__file__)), "two_orbit_results.csv")
ROWS_PER_PAGE = 1
MIN_INLIERS, MAX_FIT_ERR = 40, 10.0
SECTION_BAND = 0.6
TITLE_STYLE = "short"
MEASURED_LABEL = "orbit measured by the pipeline"
OPPOSITE_LABEL = "orbit on the opposite side"
SHOW_SIGN = False


def largest_component(file_path):
    mesh = trimesh.load_mesh(file_path)
    parts = mesh.split(only_watertight=False)
    return max(parts, key=lambda c: len(c.vertices)) if len(parts) > 1 else mesh


def lateral(ax, mesh, centre, radius, inliers, seed, title):
    view = 1.0 if centre[1] >= 0 else -1.0
    V, F = mesh.vertices, mesh.faces
    order = np.argsort((view * V[:, 1])[F].mean(axis=1))
    light = np.array([0.0, view, 0.4])
    light /= np.linalg.norm(light)
    normals = np.nan_to_num(np.asarray(mesh.face_normals, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    shade = 0.3 + 0.65 * np.clip(normals @ light, 0.0, 1.0)
    polys = np.stack([view * V[:, 0][F], V[:, 2][F]], axis=2)[order]
    colours = np.c_[np.repeat(shade[order][:, None], 3, axis=1), np.full(len(order), 0.9)]
    ax.add_collection(PolyCollection(polys, facecolors=colours, edgecolors="none"))
    t = np.linspace(0, 2 * np.pi, 200)
    ax.plot(view * centre[0] + radius * np.cos(t), centre[2] + radius * np.sin(t), "b", lw=1.5)
    ax.scatter(view * inliers[:, 0], inliers[:, 2], s=4, c="r", zorder=5)
    if seed is not None:
        ax.scatter([view * seed[0]], [seed[2]], s=28, c="limegreen", edgecolors="k", linewidths=.4, zorder=6)
    xs = view * V[:, 0]
    ax.set_xlim(xs.min() - 1, xs.max() + 1)
    ax.set_ylim(V[:, 2].min() - 1, V[:, 2].max() + 1)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title, fontsize=7)


def section(ax, mesh, first, second, title):
    centre = np.array([first["cx"], first["cy"], first["cz"]])
    try:
        cut = mesh.section(plane_origin=centre, plane_normal=[0, 0, 1])
    except Exception:
        cut = None
    if cut is not None:
        for entity in cut.entities:
            pts = cut.vertices[entity.points]
            ax.plot(pts[:, 0], pts[:, 1], "k", lw=0.6)
    t = np.linspace(0, 2 * np.pi, 200)
    ax.plot(centre[0] + first["sphere_radius"] * np.cos(t), centre[1] + first["sphere_radius"] * np.sin(t),
            "b", lw=1.6)
    near = first["_inliers"][np.abs(first["_inliers"][:, 2] - centre[2]) < SECTION_BAND]
    ax.scatter(near[:, 0], near[:, 1], s=7, c="r", zorder=5)
    if second is not None and second.get("status") == "ok":
        centre2 = np.array([second["cx"], second["cy"], second["cz"]])
        cross = np.sqrt(max(second["sphere_radius"] ** 2 - (centre2[2] - centre[2]) ** 2, 0.0))
        colour = "darkorange" if meets(second) else "0.45"
        if cross > 0:
            ax.plot(centre2[0] + cross * np.cos(t), centre2[1] + cross * np.sin(t), color=colour, ls="--", lw=1.6)
        near2 = second["_inliers"][np.abs(second["_inliers"][:, 2] - centre[2]) < SECTION_BAND]
        ax.scatter(near2[:, 0], near2[:, 1], s=7, c=colour, zorder=5)
    ax.axhline(0, color="0.75", ls=":", lw=0.8)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title, fontsize=7)


def meets(fit):
    return fit.get("status") == "ok" and fit["n_inliers"] >= MIN_INLIERS and fit["fit_err_pct"] <= MAX_FIT_ERR


def side_label(text, sign):
    return "%s (%s)" % (text, sign) if SHOW_SIGN else text


def specimen_stem(filename):
    return os.path.splitext(filename)[0].replace(" ", "").replace("/", "-")


missing = [f for f in FOLDERS if not os.path.isdir(os.path.join(DATA, f))]
if missing:
    sys.exit("folder not found: " + ", ".join(missing))

os.makedirs(os.path.join(HERE, OUT_DIR), exist_ok=True)
jobs = []
for folder in FOLDERS:
    for fp in sorted(glob.glob(os.path.join(DATA, folder, "*.stl"))):
        jobs.append((folder, fp))
print("%d skulls in %d folders" % (len(jobs), len(FOLDERS)))

rows, page_rows, page_no, current_folder = [], [], 0, None
fig = axs = pdf = None


def open_output(folder):
    global pdf, page_no
    page_no = 0
    if OUTPUT == "pdf":
        from matplotlib.backends.backend_pdf import PdfPages
        path = os.path.join(HERE, OUT_DIR, "%s_%s.pdf" % (PREFIX, LABELS.get(folder, folder)))
        pdf = PdfPages(path)
        print("  writing", path)


def close_output():
    global pdf
    if pdf is not None:
        pdf.close()
        pdf = None


def new_page():
    global fig, axs, page_rows
    fig, axs = plt.subplots(ROWS_PER_PAGE, 3, figsize=(15, 4.4 * ROWS_PER_PAGE), squeeze=False)
    for row in axs:
        for ax in row:
            ax.axis("off")
    page_rows = []


def save_page(folder):
    global page_no
    if fig is None or not page_rows:
        return
    page_no += 1
    label = LABELS.get(folder, folder)
    fig.tight_layout()
    if OUTPUT == "pdf":
        pdf.savefig(fig)
    else:
        if ROWS_PER_PAGE == 1:
            fname = "%s_%s_%s.png" % (PREFIX, label, specimen_stem(page_rows[0]))
        else:
            fname = "%s_%s_p%02d.png" % (PREFIX, label, page_no)
        out = os.path.join(HERE, OUT_DIR, fname)
        fig.savefig(out, dpi=100)
        print("  ->", out)
    if SHOW:
        plt.show()
    plt.close(fig)


for i, (folder, fp) in enumerate(jobs, 1):
    name = os.path.basename(fp)
    if folder != current_folder:
        save_page(current_folder)
        close_output()
        current_folder = folder
        open_output(folder)
        new_page()
    elif len(page_rows) == ROWS_PER_PAGE:
        save_page(folder)
        new_page()

    mesh = largest_component(fp)
    first = run(fp)
    row = dict(filename=name, folder=folder, group=LABELS.get(folder, folder), status=first.get("status", "fail"))
    r = len(page_rows)

    if first.get("status") != "ok":
        axs[r][0].text(.5, .5, "%s\nno fit" % name, ha="center", va="center", fontsize=8)
        rows.append(row); page_rows.append(name)
        print("[%d/%d] %s: no fit" % (i, len(jobs), name), flush=True)
        continue

    centre = np.array([first["cx"], first["cy"], first["cz"]])
    side = "y<0" if first["cy"] < 0 else "y>0"
    other = "y>0" if first["cy"] < 0 else "y<0"
    ok1 = meets(first)
    second = run(fp, half=other)

    if TITLE_STYLE == "short":
        title_first = "%s\n%s" % (name, side_label(MEASURED_LABEL, side))
    else:
        title_first = ("%s\npipeline fit (%s): r = %.2f mm, %d inliers, error %.1f%%  [%s]"
                       % (name, side_label(MEASURED_LABEL, side), first["sphere_radius"], first["n_inliers"],
                          first["fit_err_pct"], "criteria met" if ok1 else "FLAGGED"))
    lateral(axs[r][0], mesh, centre, first["sphere_radius"], first["_inliers"], first.get("_seed"), title_first)

    row.update(r_pipeline=first["sphere_radius"], side_pipeline=side,
               n_inliers_pipeline=first["n_inliers"], fit_err_pct_pipeline=first["fit_err_pct"],
               pipeline_meets_criteria=int(ok1))

    if second.get("status") == "ok":
        centre2 = np.array([second["cx"], second["cy"], second["cz"]])
        disagreement = 100 * abs(second["sphere_radius"] - first["sphere_radius"]) / first["sphere_radius"]
        ok2 = meets(second)
        if TITLE_STYLE == "short":
            title_second = "%s\n%s" % (name, side_label(OPPOSITE_LABEL, other))
        else:
            title_second = ("other side (%s): r = %.2f mm, %d inliers, error %.1f%%\ndisagreement %.1f%%  [%s]"
                            % (side_label(OPPOSITE_LABEL, other), second["sphere_radius"], second["n_inliers"],
                               second["fit_err_pct"], disagreement, "criteria met" if ok2 else "criteria NOT met"))
        lateral(axs[r][2], mesh, centre2, second["sphere_radius"], second["_inliers"], second.get("_seed"), title_second)
        row.update(r_second=second["sphere_radius"], n_inliers_second=second["n_inliers"],
                   fit_err_pct_second=second["fit_err_pct"], second_meets_criteria=int(ok2),
                   disagreement_pct=disagreement)
        print("[%d/%d] %s: %.2f vs %.2f mm (%.1f%%)" % (i, len(jobs), name, first["sphere_radius"],
                                                        second["sphere_radius"], disagreement), flush=True)
    else:
        axs[r][2].text(.5, .5, "%s\n%s: no fit" % (name, side_label(OPPOSITE_LABEL, other)),
                       ha="center", va="center", fontsize=8)
        row.update(second_meets_criteria=0, disagreement_pct=np.nan)
        print("[%d/%d] %s: %.2f mm, no fit on %s" % (i, len(jobs), name, first["sphere_radius"], other), flush=True)

    section(axs[r][1], mesh, first, second,
            "both orbits" if TITLE_STYLE == "short" else
            "horizontal slice through the sphere centre, seen from above\nblue = pipeline fit, dashed = other side")

    rows.append(row); page_rows.append(name)

save_page(current_folder)
close_output()

d = pd.DataFrame(rows)
export_measurements(d).to_csv(os.path.join(HERE, CSV), index=False)
print("written", os.path.join(HERE, CSV), "(%d rows)" % len(d))

from scipy.stats import spearmanr
s = d[(d.status == "ok") & (~d.filename.str.contains("Peromyscus", case=False))].copy()
s["finch"] = s.folder.str.contains(FINCH_FOLDERS, case=False)
s["loxops"] = s.filename.str.contains("caeruleirostris|coccineus")
print("\nprimary fits meeting the criteria: %d of %d" % (int(s.pipeline_meets_criteria.sum()), len(s)))
for label, part in [("finch specimens", s[s.finch]), ("other skulls (excl. Loxops)", s[~s.finch & ~s.loxops])]:
    ok = part[part.second_meets_criteria == 1]
    if len(ok) == 0:
        continue
    print("%-28s second orbit meeting the criteria: %d of %d | disagreement: median %.1f%%, 75th %.1f%%, "
          "90th %.1f%% | Spearman between sides %.2f"
          % (label, len(ok), len(part), ok.disagreement_pct.median(), ok.disagreement_pct.quantile(.75),
             ok.disagreement_pct.quantile(.9), spearmanr(ok.r_pipeline, ok.r_second).correlation))
