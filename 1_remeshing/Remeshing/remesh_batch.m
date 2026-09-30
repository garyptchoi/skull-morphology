function remesh_batch(in_dir, out_dir, param_csv, varargin)

addpath(genpath(fullfile(fileparts(mfilename('fullpath')), 'code')));
if exist('polygon2voxel_double', 'file') ~= 3
    error('remesh_batch:setup', 'Run setup_remeshing in 1_remeshing/Remeshing first.');
end

p = inputParser;
addParameter(p, 'MeshFix', true);
addParameter(p, 'Rescale', false);
addParameter(p, 'RescaleMode', 'uniform');
addParameter(p, 'Overwrite', false);
addParameter(p, 'Seed', 0);
addParameter(p, 'Threads', []);
parse(p, varargin{:});
opt = p.Results;

if nargin < 3, param_csv = ''; end
if ~exist(out_dir, 'dir'), mkdir(out_dir); end

if ~isempty(opt.Threads), maxNumCompThreads(opt.Threads); end
stamp = char(datetime('now', 'Format', 'yyyy-MM-dd HH:mm:ss'));
fs = fopen(fullfile(out_dir, 'remeshing_settings.txt'), 'a');
fprintf(fs, '%s  MATLAB %s  MeshFix=%d Rescale=%d RescaleMode=%s Seed=%d Threads=%d  in=%s\n', stamp, version, ...
    double(opt.MeshFix), double(opt.Rescale), opt.RescaleMode, opt.Seed, maxNumCompThreads, in_dir);
fclose(fs);

para_map = containers.Map('KeyType', 'char', 'ValueType', 'any');
if ~isempty(param_csv) && exist(param_csv, 'file')
    T = readtable(param_csv, 'TextType', 'string');
    for i = 1:height(T)
        reason = '';
        if any(strcmp(T.Properties.VariableNames, 'reason')), reason = char(T.reason(i)); end
        para_map(char(T.filename(i))) = struct('para', T.para(i), 'reason', reason);
    end
end

files = dir(fullfile(in_dir, '*.stl'));
files = natsortfiles({files.name})';
fprintf('%d files in %s\n', numel(files), in_dir);

logfile = fullfile(out_dir, 'remeshing_log.csv');
hdr = 'filename,output,para,seed,reason,n_vertices,n_faces,euler,genus,change_gen,meshfix_applied,note,seconds,status';
if exist(logfile, 'file')
    f0 = fopen(logfile, 'r'); first = fgetl(f0); fclose(f0);
    if ischar(first) && ~strcmp(strtrim(first), hdr)
        bak = fullfile(out_dir, ['remeshing_log_old_' char(datetime('now', 'Format', 'yyyyMMdd_HHmmss')) '.csv']);
        movefile(logfile, bak);
        fprintf('old log has a different header, moved to %s\n', bak);
    end
end
fid = fopen(logfile, 'a');
if ftell(fid) == 0, fprintf(fid, '%s\n', hdr); end

for i = 1:numel(files)
    name = files{i}(1:end-4);
    para = 60; reason = '';
    if isKey(para_map, files{i}), s = para_map(files{i}); para = s.para; reason = s.reason; end
    out_name = sprintf('%s_p%d.stl', name, para);
    out_file = fullfile(out_dir, out_name);
    if exist(out_file, 'file') && ~opt.Overwrite
        fprintf('[%d/%d] %s exists, skipped\n', i, numel(files), out_name); continue;
    end
    fprintf('[%d/%d] %s  para=%d ... ', i, numel(files), name, para);
    rng(opt.Seed, 'twister');
    t0 = tic; note = ''; fixed = 0; genus = NaN; change_gen = NaN;
    try
        [v_ori, f_ori] = stlRead(fullfile(in_dir, files{i}));

        [~, ~, fvox, ~, ~, genus, ~, change_gen, vvox] = voxelelize_genus(v_ori, f_ori, para, 1, 1);

        vvox_sm = laplacian_smooth(vvox, fvox, 'cotan', [], 0.05, 'implicit', vvox, 15);
        v = vvox_sm;
        f = fliplr(fvox);

        euler = size(v,1) - 3*size(f,1)/2 + size(f,1);
        if euler ~= 2
            if ~isempty(meshboundaries(f))
                note = 'boundary';
            elseif ~isempty(setdiff(1:size(v,1), unique(f(:))))
                note = 'unreferenced vertices';
            else
                e = sort(cat(1, f(:,1:2), f(:,2:3), f(:,[3 1])), 2);
                unqEdges = unique(e, 'rows');
                if size(e,1) ~= size(unqEdges,1)*2, note = 'non-manifold'; else, note = 'genus>=1 or multiple components'; end
            end
            if opt.MeshFix
                [v, f] = meshcheckrepair(v, f, 'meshfix');
                fixed = 1;
                euler = size(v,1) - 3*size(f,1)/2 + size(f,1);
            end
        end

        if opt.Rescale
            [TR, TT] = icp_matlabcentral(v_ori', v', 20);
            v = (TR * v' + TT)';

            e = v_ori([f_ori(:,1); f_ori(:,2); f_ori(:,3)], :) - v_ori([f_ori(:,2); f_ori(:,3); f_ori(:,1)], :);
            e = sqrt(sum(e.^2, 2));
            G = sparse([f_ori(:,1); f_ori(:,2); f_ori(:,3)], [f_ori(:,2); f_ori(:,3); f_ori(:,1)], ...
                double(e < (mean(e) + 3*std(e))), size(v_ori,1), size(v_ori,1));
            G(G ~= 0) = 1;
            [bins, binsizes] = conncomp(graph(G + G'));
            [~, big] = max(binsizes);
            v_core = v_ori(bins == big, :);
            mid = (max(v) + min(v)) / 2;
            fac = (max(v_core) - min(v_core)) ./ (max(v) - min(v));
            if strcmpi(opt.RescaleMode, 'uniform'), fac = repmat(mean(fac), 1, 3); end
            v = (v - mid) .* fac + mid;
        end

        stlWrite(out_file, f, v);
        secs = toc(t0);
        fprintf('%d vertices, euler %g, genus %g, %.1f s\n', size(v,1), euler, genus, secs);
        fprintf(fid, '%s,%s,%d,%d,%s,%d,%d,%g,%g,%g,%d,%s,%.1f,ok\n', files{i}, out_name, para, opt.Seed, reason, ...
            size(v,1), size(f,1), euler, genus, change_gen, fixed, note, secs);
    catch ME
        secs = toc(t0);
        fprintf('FAILED: %s\n', ME.message);
        fprintf(fid, '%s,%s,%d,%d,%s,,,,,,,,%.1f,failed: %s\n', files{i}, out_name, para, opt.Seed, reason, secs, ...
            strrep(ME.message, ',', ';'));
    end
end
fclose(fid);
fprintf('log written to %s\n', logfile);
end
