function test_remeshing
setup_remeshing('DownloadMeshFix', false);
work = tempname;
mkdir(work);
cleanup = onCleanup(@()rmdir(work, 's'));
input_dir = fullfile(work, 'input');
output_dir = fullfile(work, 'output');
mkdir(input_dir);

[x, y, z] = sphere(10);
v = unique([x(:), y(:), z(:)], 'rows');
f = convhull(v);
[vf, ff] = meshcheckrepair(v, f, 'meshfix');
assert(~isempty(vf) && ~isempty(ff), 'MeshFix did not return a surface.');
stlWrite(fullfile(input_dir, 'sphere.stl'), f, v);
params = table({'sphere.stl'}, 20, {'smoke test'}, ...
    'VariableNames', {'filename', 'para', 'reason'});
params_file = fullfile(work, 'params.csv');
writetable(params, params_file);
remesh_batch(input_dir, output_dir, params_file, 'Seed', 0);

result = fullfile(output_dir, 'sphere_p20.stl');
assert(isfile(result), 'Batch remeshing did not produce the expected STL.');
[vr, fr] = stlRead(result);
assert(all(isfinite(vr(:))) && ~isempty(fr), 'The remeshed surface is invalid.');
assert(isempty(meshboundaries(fr)), 'The remeshed surface has a boundary.');
assert(calc_genus(vr, fr) == 0, 'The remeshed surface is not genus zero.');
log = readtable(fullfile(output_dir, 'remeshing_log.csv'), 'TextType', 'string');
assert(height(log) == 1 && log.status(1) == "ok", 'The batch log reports a failure.');
assert(log.para(1) == 20 && log.seed(1) == 0, 'The batch settings were not applied.');
fprintf('Synthetic-sphere remeshing test passed. Inspect anatomical results separately.\n');
end
