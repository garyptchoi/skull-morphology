
import trimesh
import pyvista as pv
import os

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paths

if __name__ == '__main__':

    FILE_PATH = str(paths.FINCHES / "G.SeptentrionalistA.stl")

    ENABLE_VISUALIZATION = True

    if not os.path.exists(FILE_PATH):
        exit(f"Error: File not found at {FILE_PATH}")

    print(f"--- Processing: {os.path.basename(FILE_PATH)} ---")

    try:
        original_mesh = trimesh.load_mesh(FILE_PATH)

        components = original_mesh.split(only_watertight=False)
        if len(components) > 1:
            print(f"  -> Mesh has {len(components)} components. Keeping the largest one.")
            processed_mesh = sorted(components, key=lambda c: len(c.vertices), reverse=True)[0]
        else:
            processed_mesh = original_mesh
        processed_mesh.process(validate=True)
        print("  -> Mesh loaded successfully.")

    except Exception as e:
        print(f"  -> Error loading or processing mesh. Error: {e}")
        processed_mesh = None

    if ENABLE_VISUALIZATION and processed_mesh:
        plotter = pv.Plotter()
        plotter.add_text("Mesh with Axis-Aligned Bounding Box (AABB)")

        plotter.add_mesh(processed_mesh, style='surface', opacity=0.4, color='lightgrey')


        bounds = processed_mesh.bounds.flatten()

        center_x = (bounds[0] + bounds[3]) / 2.0
        center_y = (bounds[1] + bounds[4]) / 2.0
        center_z = (bounds[2] + bounds[5]) / 2.0
        center = [center_x, center_y, center_z]

        length_x = bounds[3] - bounds[0]
        length_y = bounds[4] - bounds[1]
        length_z = bounds[5] - bounds[2]

        aabb_cube = pv.Cube(center=(0, 0, 0), x_length=length_x, y_length=length_y, z_length=length_z)

        aabb_cube.translate(center, inplace=True)

        plotter.add_mesh(aabb_cube, style='wireframe', color='red', line_width=2,
                         label='Axis-Aligned Bounding Box (AABB)')


        plotter.add_legend()
        plotter.show(cpos='xy')

    elif not processed_mesh:
        print("  -> Visualization skipped because mesh could not be loaded.")

    print("\n--- Processing complete. ---")
