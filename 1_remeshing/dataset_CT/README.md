# 1_remeshing/dataset_CT/

Drop raw scan meshes here (.stl, .ply, .obj or .off). `remesh_in_pycharm.py` (or
`remesh_human_head_in_pycharm.py` for human crania) writes remeshed STLs and run logs
to `dataset_remeshed/`. These scripts stop after remeshing. Run fitting separately
using the scripts in `2_fitting/`.

When a remeshed skull is final, copy it into the matching folder of `data/`, where every other
step reads it.
