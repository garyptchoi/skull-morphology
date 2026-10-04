#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
from pathlib import Path

_THIS_FILE = globals().get("__file__", os.path.join(os.getcwd(), "demo_animation.py"))
HERE = Path(_THIS_FILE).resolve().parent
sys.path.insert(0, str(HERE.parents[0]))
sys.path.insert(0, str(HERE))
import paths

os.environ.setdefault("MPLBACKEND", "Agg")
import numpy as np
import trimesh
import pyvista as pv
from PIL import Image, ImageDraw, ImageFont
from matplotlib import font_manager

import figure as F

SKULL = "G.DifficilisA"
SKULL_NAME = ("Geospiza difficilis", "Darwin's finch")
OTHERS = [
    (paths.FINCHES / "G.MagnirostrisA.stl", "Geospiza magnirostris", "Darwin's finch"),
    (paths.HONEYCREEPERS / 'H.wilsoniB.stl', "Hemignathus wilsoni", "Hawaiian honeycreeper"),
    (paths.HONEYCREEPERS / 'L. caeruleirostrisA.stl', "Loxops caeruleirostris", "honeycreeper, damaged skull"),
    ("BodyParts3D", "Homo sapiens", "human cranium"),
]
WIDTH, HEIGHT = 800, 450
SUPERSAMPLE = 2
FPS = 25
GIF_FPS = 10
GIF_WIDTH = 720
SKULL_FILL = 0.56
VIEW_ANGLE = 20.0

SCENES = [("skull", 2.0), ("box", 2.6), ("concave", 3.0), ("sphere", 3.4), ("ellipsoid", 3.4),
          ("others", 3.6), ("loop", 0.8)]

BONE = np.array([225, 222, 214]) / 255.0
CONCAVE = np.array([40, 110, 200]) / 255.0
DIMMED = np.array([240, 239, 236]) / 255.0
BOX_RED = "#e3120b"
SPHERE_BLUE = "#1d3fd6"
INLIER_RED = "#dc143c"
SEED_GREEN = "#32cd32"
AXIS_COLOURS = ("#e3120b", "#1a9641", "#1d3fd6")
TEXT_DARK, TEXT_GREY, ACCENT = (34, 34, 34), (110, 110, 110), (29, 63, 214)

OUT = paths.output_dir(_THIS_FILE)
FRAMES = OUT / "frames"


def ease(t):
    t = float(np.clip(t, 0.0, 1.0))
    return 0.5 - 0.5 * np.cos(np.pi * t)


def ramp(t, start, length):
    return ease((t - start) / length) if length > 0 else float(t >= start)


def font(size, italic=False, bold=False):
    prop = font_manager.FontProperties(family=["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
                                       style="italic" if italic else "normal", weight="bold" if bold else "normal")
    return ImageFont.truetype(font_manager.findfont(prop), size)


def pv_mesh(mesh):
    faces = np.hstack([np.full((len(mesh.faces), 1), 3), mesh.faces]).ravel()
    return pv.PolyData(np.asarray(mesh.vertices, float), faces)


def wire_sphere(n=30):
    return pv.Sphere(radius=1.0, theta_resolution=n, phi_resolution=n).extract_all_edges()


def camera_on(plotter, focal, direction, distance, up=(0.0, 0.0, 1.0)):
    d = np.asarray(direction, float); d /= np.linalg.norm(d)
    plotter.camera.focal_point = tuple(focal)
    plotter.camera.position = tuple(np.asarray(focal) + distance * d)
    plotter.camera.up = up
    plotter.camera.view_angle = VIEW_ANGLE


def distance_for(width_mm, fill, aspect):
    return width_mm / (fill * 2 * np.tan(np.radians(VIEW_ANGLE / 2)) * aspect)


def lateral_direction(side, azimuth_deg, elevation_deg):
    a, e = np.radians(azimuth_deg), np.radians(elevation_deg)
    return np.array([np.cos(e) * np.sin(a), side * np.cos(e) * np.cos(a), np.sin(e)])


def screenshot(plotter):
    img = plotter.screenshot(return_img=True)
    return Image.fromarray(img).convert("RGB")


def measure_skull(path):
    m = F.load_big(str(path))
    orbit = F.run(str(path))
    brain = F.fit_ellipsoid(str(path))
    if orbit.get("status") != "ok" or brain.get("status") != "ok":
        raise RuntimeError(f"no fit on {path}")
    V = m.vertices
    H = trimesh.curvature.discrete_mean_curvature_measure(m, V, radius=2.0)
    lo, hi = V[:, 0].min(), V[:, 0].max()
    band = (V[:, 0] > lo + 0.30 * (hi - lo)) & (V[:, 0] < lo + 0.70 * (hi - lo))
    return dict(mesh=m, orbit=orbit, brain=brain, curvature=H, band=band, bounds=m.bounds,
                band_x=(lo + 0.30 * (hi - lo), lo + 0.70 * (hi - lo)))


class PipelineScene:
    def __init__(self, S):
        self.S = S
        W, H = WIDTH * SUPERSAMPLE, HEIGHT * SUPERSAMPLE
        p = self.p = pv.Plotter(off_screen=True, window_size=(W, H))
        p.set_background("white")
        m, o, b = S["mesh"], S["orbit"], S["brain"]
        self.skull = pv_mesh(m)
        self.skull.point_data["colours"] = np.tile((BONE * 255).astype(np.uint8), (len(m.vertices), 1))
        self.skull_actor = p.add_mesh(self.skull, scalars="colours", rgb=True, smooth_shading=True,
                                      specular=0.25, specular_power=20, ambient=0.15)
        (x0, y0, z0), (x1, y1, z1) = S["bounds"]
        self.box_actor = p.add_mesh(pv.Box((x0, x1, y0, y1, z0, z1)).extract_all_edges(), color=BOX_RED,
                                    line_width=2.2 * SUPERSAMPLE)
        planes = pv.MultiBlock()
        for xb in S["band_x"]:
            planes.append(pv.Plane(center=(xb, (y0 + y1) / 2, (z0 + z1) / 2), direction=(1, 0, 0),
                                   i_size=(z1 - z0) * 1.15, j_size=(y1 - y0) * 1.15))
        self.band_actor = p.add_mesh(planes.combine(), color="#9ecae1", opacity=0.0, show_edges=False,
                                     lighting=False)
        self.c = np.array([o["cx"], o["cy"], o["cz"]]); self.r = o["sphere_radius"]
        self.seed_actor = p.add_mesh(pv.Sphere(radius=0.45, center=o["_seed"]), color=SEED_GREEN,
                                     smooth_shading=True)
        self.inlier_actor = p.add_points(np.asarray(o["_inliers"], float), color=INLIER_RED,
                                         point_size=5.0 * SUPERSAMPLE, render_points_as_spheres=True)
        self.unit = wire_sphere(30)
        self.sphere = self.unit.copy()
        self.sphere_actor = p.add_mesh(self.sphere, color=SPHERE_BLUE, line_width=1.1 * SUPERSAMPLE)
        self.ec, self.ea = np.asarray(b["center"], float), np.asarray(b["axes"], float)
        self.ellipsoid = self.unit.copy()
        self.ellipsoid_actor = p.add_mesh(self.ellipsoid, color=SPHERE_BLUE, line_width=1.1 * SUPERSAMPLE)
        self.axis_actors = []
        for k, col in enumerate(AXIS_COLOURS):
            d = np.zeros(3); d[k] = self.ea[k]
            self.axis_actors.append(p.add_mesh(pv.Line(self.ec - d, self.ec + d), color=col,
                                               line_width=3.0 * SUPERSAMPLE))
        length = np.ptp(S["bounds"][:, 0])
        self.distance = distance_for(length, SKULL_FILL, WIDTH / HEIGHT)
        self.focal = np.asarray(S["bounds"]).mean(axis=0) - np.array([0, 0, 0.07 * length])
        self.side = -1.0 if self.c[1] < 0 else 1.0

    def frame(self, t, times):
        S, p = self.S, self.p
        tb, tc, ts, te = times["box"], times["concave"], times["sphere"], times["ellipsoid"]
        az = -40.0 + 55.0 * ease(t / times["box"])
        camera_on(p, self.focal, lateral_direction(self.side, az, 14.0), self.distance)
        k_conc = ramp(t, tc + 0.1, 0.7) * (1 - ramp(t, ts + 0.9, 0.7))
        concave = np.clip(-S["curvature"] / 4.0, 0, 1)[:, None]
        coloured = BONE * (1 - concave) + CONCAVE * concave
        coloured = np.where(S["band"][:, None], coloured, DIMMED)
        rgb = BONE * (1 - k_conc) + coloured * k_conc
        self.skull.point_data["colours"] = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
        self.skull_actor.prop.opacity = 1.0 - 0.45 * ramp(t, tb, 0.5) * (1 - ramp(t, tc, 0.5)) \
            - 0.5 * ramp(t, te + 0.2, 0.6)
        self.box_actor.prop.opacity = ramp(t, tb + 0.2, 0.6) * (1 - ramp(t, tc, 0.5))
        self.box_actor.SetVisibility(self.box_actor.prop.opacity > 0.01)
        self.band_actor.prop.opacity = 0.35 * ramp(t, tc + 0.3, 0.6) * (1 - ramp(t, ts + 0.9, 0.6))
        self.band_actor.SetVisibility(self.band_actor.prop.opacity > 0.01)
        self.seed_actor.SetVisibility(ts - 0.4 <= t < te + 0.3)
        k_in = ramp(t, ts + 0.3, 0.4) * (1 - ramp(t, te, 0.4))
        self.inlier_actor.prop.opacity = k_in
        self.inlier_actor.SetVisibility(k_in > 0.01)
        g = ramp(t, ts + 0.9, 1.0)
        self.sphere.points = self.c + self.unit.points * max(g, 1e-3) * self.r
        self.sphere_actor.SetVisibility(g > 0.01)
        self.sphere_actor.prop.opacity = 1.0 - 0.7 * ramp(t, te, 0.5)
        ge = ramp(t, te + 0.4, 1.0)
        self.ellipsoid.points = self.ec + self.unit.points * self.ea * max(ge, 1e-3)
        self.ellipsoid_actor.SetVisibility(ge > 0.01)
        for a in self.axis_actors:
            a.SetVisibility(ge > 0.99)
        p.render()
        return screenshot(p)


CAPTION_BAND = 84


class OtherSkull:
    def __init__(self, spec):
        what, self.name, self.group = spec
        W, H = WIDTH * SUPERSAMPLE // 2, (HEIGHT - CAPTION_BAND) * SUPERSAMPLE // 2
        p = self.p = pv.Plotter(off_screen=True, window_size=(W, H))
        p.set_background("white")
        if isinstance(what, str):
            h = next(h for h in F.human_results() if h["name"] == what)
            m, fit = F.mesh_of(h["path"]), h
            self.human = True
        else:
            m, fit = F.load_big(str(what)), F.run(str(what))
            self.human = False
        c, r = np.array([fit["cx"], fit["cy"], fit["cz"]]), fit["sphere_radius"]
        p.add_mesh(pv_mesh(m), color=BONE, smooth_shading=True, specular=0.25, specular_power=20, ambient=0.15)
        p.add_mesh(wire_sphere(24).scale(r, inplace=False).translate(c, inplace=False), color=SPHERE_BLUE,
                   line_width=1.0 * SUPERSAMPLE)
        p.add_mesh(pv.Sphere(radius=0.13 * r, center=fit["_seed"]), color=SEED_GREEN, smooth_shading=True)
        V = m.vertices
        self.focal = m.bounds.mean(axis=0)
        self.extent = np.ptp(V, axis=0)
        if self.human:
            self.side = 1.0 if c[1] >= V[:, 1].mean() else -1.0
        else:
            self.side = -1.0 if c[1] < 0 else 1.0
        self.mirror = (not self.human) and self.side > 0

    def frame(self, t):
        W, H = self.p.window_size
        turn = np.radians(-12.0 + 24.0 * t / dict(SCENES)["others"])
        if self.human:
            a = np.radians(35.0)
            base = np.array([-np.cos(a), self.side * np.sin(a), 0.3])
            rot = np.array([[np.cos(turn), -np.sin(turn), 0], [np.sin(turn), np.cos(turn), 0], [0, 0, 1]])
            direction = rot @ base
            distance = distance_for(self.extent[2], 0.78, 1.0)
        else:
            direction = lateral_direction(self.side, np.degrees(turn), 14.0)
            distance = distance_for(self.extent[0], 0.62, W / H)
        camera_on(self.p, self.focal, direction, distance)
        self.p.render()
        img = screenshot(self.p)
        return img.transpose(Image.FLIP_LEFT_RIGHT) if self.mirror else img


CAPTIONS = {
    "skull": ("Input: a 3D skull mesh", "one of the 100 skulls of Darwin's finches and their relatives"),
    "box": ("1  Skull size", "bounding box: length {L:.1f} mm, width {W:.1f} mm, height {H:.1f} mm"),
    "concave": ("2  Where is the orbit?", "the most concave surface in the middle 30–70% of the skull"),
    "sphere": ("3  Orbit", "sphere fitted to the concave patch: radius {r:.2f} mm"),
    "ellipsoid": ("4  Braincase", "ellipsoid fitted to the rear of the skull: semi-axes {a:.1f}, {b:.1f}, {c:.1f} mm"),
    "others": ("The same code on other skulls", "Darwin's finches, Hawaiian honeycreepers (also damaged ones) "
                                                 "and human crania"),
}


def draw_caption(img, title, text, alpha, species=None):
    s = SUPERSAMPLE
    layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
    d = ImageDraw.Draw(layer)
    a = int(255 * alpha)
    d.text((28 * s, img.size[1] - 66 * s), title, font=font(22 * s, bold=True), fill=ACCENT + (a,))
    d.text((28 * s, img.size[1] - 36 * s), text, font=font(17 * s), fill=TEXT_DARK + (a,))
    if species:
        d.text((28 * s, 22 * s), species[0], font=font(19 * s, italic=True), fill=TEXT_DARK + (255,))
        d.text((28 * s, 46 * s), species[1], font=font(15 * s), fill=TEXT_GREY + (255,))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def label_panel(img, name, group):
    s = SUPERSAMPLE
    d = ImageDraw.Draw(img)
    d.text((14 * s, 10 * s), name, font=font(15 * s, italic=True), fill=TEXT_DARK)
    d.text((14 * s, 30 * s), group, font=font(12 * s), fill=TEXT_GREY)
    return img


def main():
    pv.OFF_SCREEN = True
    path = paths.FINCHES / f"{SKULL}.stl"
    print(f"measuring {path.name} ...", flush=True)
    S = measure_skull(path)
    L, W, H = np.ptp(S["bounds"], axis=0)
    o, b = S["orbit"], S["brain"]
    values = dict(L=L, W=W, H=H, r=o["sphere_radius"], a=b["axes"][0], b=b["axes"][1], c=b["axes"][2])
    print(f"  box {L:.2f} x {W:.2f} x {H:.2f} mm, orbit radius {o['sphere_radius']:.3f} mm "
          f"({o['n_inliers']} inliers), ellipsoid {b['axes'][0]:.2f}, {b['axes'][1]:.2f}, {b['axes'][2]:.2f} mm")

    times, t0 = {}, 0.0
    for name, dur in SCENES:
        times[name] = t0; t0 += dur
    total = t0
    n_frames = int(round(total * FPS))

    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir(parents=True)
    scene = PipelineScene(S)
    print("drawing the other skulls ...", flush=True)
    others = [OtherSkull(spec) for spec in OTHERS]
    size = (WIDTH * SUPERSAMPLE, HEIGHT * SUPERSAMPLE)
    white = Image.new("RGB", size, "white")

    def dip(a, b, u):
        return Image.blend(a, white, ease(u / 0.5)) if u < 0.5 else Image.blend(white, b, ease((u - 0.5) / 0.5))

    first = last_pipeline = last_others = None
    print(f"drawing {n_frames} frames ...", flush=True)
    for i in range(n_frames):
        t = i / FPS
        name = max((n for n, _ in SCENES if times[n] <= t), key=lambda n: times[n])
        if name in ("skull", "box", "concave", "sphere", "ellipsoid"):
            img = scene.frame(t, times)
            k = dict(SCENES)[name]
            fade_in = 1.0 if name in ("skull", "ellipsoid") else ramp(t, times[name], 0.35)
            fade_out = 1.0 if name == "ellipsoid" else 1 - ramp(t, times[name] + k - 0.3, 0.3)
            title, text = CAPTIONS[name]
            img = draw_caption(img, title, text.format(**values), min(fade_in, fade_out), SKULL_NAME)
            last_pipeline = img
        else:
            tt = t - times["others"]
            grid = Image.new("RGB", size, "white")
            for k, other in enumerate(others):
                panel = label_panel(other.frame(min(tt, dict(SCENES)["others"])), other.name, other.group)
                grid.paste(panel, ((k % 2) * panel.size[0], (k // 2) * panel.size[1]))
            title, text = CAPTIONS["others"]
            grid = draw_caption(grid, title, text, 1.0)
            if name == "others":
                img = dip(last_pipeline, grid, tt / 0.6) if tt < 0.6 else grid
                last_others = grid
            else:
                img = dip(last_others, first, (t - times["loop"]) / dict(SCENES)["loop"])
        if i == 0:
            first = img
        img.resize((WIDTH, HEIGHT), Image.LANCZOS).save(FRAMES / f"frame_{i:04d}.png")
        if i % 50 == 0:
            print(f"  {i}/{n_frames}", flush=True)

    write_gif_and_mp4(n_frames)


def write_gif_and_mp4(n_frames):
    gif, mp4 = OUT / "demo.gif", OUT / "demo.mp4"
    if shutil.which("ffmpeg"):
        pattern = str(FRAMES / "frame_%04d.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", pattern,
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", str(mp4)],
                       check=True)
        palette = OUT / "palette.png"
        vf = f"fps={GIF_FPS},scale={GIF_WIDTH}:-1:flags=lanczos"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", pattern,
                        "-vf", vf + ",palettegen=stats_mode=diff", str(palette)], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", pattern, "-i", str(palette),
                        "-lavfi", vf + " [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                        "-loop", "0", str(gif)], check=True)
        palette.unlink()
    else:
        step = FPS / GIF_FPS
        size = (GIF_WIDTH, int(round(GIF_WIDTH * HEIGHT / WIDTH)))
        imgs = [Image.open(FRAMES / f"frame_{int(round(k * step)):04d}.png").convert("RGB").resize(size, Image.LANCZOS)
                .quantize(colors=128) for k in range(int(n_frames / step))]
        imgs[0].save(gif, save_all=True, append_images=imgs[1:], duration=int(1000 / GIF_FPS), loop=0,
                     optimize=True)
        print("ffmpeg not found: demo.gif written by Pillow, and no demo.mp4 (install ffmpeg for both)")
        mp4 = None
    for f in (gif, mp4):
        if f is not None and f.exists():
            print(f"written: {f}  ({f.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
