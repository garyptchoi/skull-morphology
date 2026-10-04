# 1_remeshing/dataset_CT/

Drop raw scan meshes here (.stl, .ply, .obj or .off). Use `remesh_in_pycharm.py`
for both bird and human meshes. It writes remeshed STLs and run logs to
`dataset_remeshed/` and stops after remeshing. Run fitting separately
using the scripts in `2_fitting/`.

When a remeshed skull is final, copy it into the matching folder of `data/`, where every other
step reads it.
