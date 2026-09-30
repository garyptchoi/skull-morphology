function setup_remeshing(varargin)
p = inputParser;
addParameter(p, 'RebuildMex', false, @(x)islogical(x) && isscalar(x));
addParameter(p, 'MeshFix', true, @(x)islogical(x) && isscalar(x));
addParameter(p, 'DownloadMeshFix', true, @(x)islogical(x) && isscalar(x));
parse(p, varargin{:});
opt = p.Results;

root = fileparts(mfilename('fullpath'));
addpath(genpath(fullfile(root, 'code')));
if verLessThan('matlab', '9.10')
    error('setup_remeshing:version', 'MATLAB R2021a or later is required for cyclebasis.');
end
required = {'imfill', 'bwconncomp', 'bwboundaries', 'padarray', 'pdist', 'squareform'};
for i = 1:numel(required)
    if isempty(which(required{i}))
        error('setup_remeshing:toolbox', ...
            '%s is missing. Install Image Processing Toolbox and Statistics and Machine Learning Toolbox.', required{i});
    end
end

voxel_dir = fullfile(root, 'code', 'voxelization');
if opt.RebuildMex || exist('polygon2voxel_double', 'file') ~= 3
    clear polygon2voxel_double
    try
        mex('-outdir', voxel_dir, fullfile(voxel_dir, 'polygon2voxel_double.c'));
        rehash;
    catch ME
        error('setup_remeshing:compiler', ...
            'Voxelizer build failed. Run mex -setup C, then setup_remeshing(''RebuildMex'', true).\n%s', ME.message);
    end
end
try
    FV.vertices = [2 2 2; 5 2 2; 2 5 2; 2 2 5];
    FV.faces = [1 3 2; 1 2 4; 1 4 3; 2 3 4];
    voxels = polygon2voxel(FV, [8 8 8], 'none');
    assert(any(voxels(:)), 'Voxelizer returned an empty volume.');
catch ME
    error('setup_remeshing:voxelizer', ...
        'Voxelizer could not run. Run mex -setup C, then setup_remeshing(''RebuildMex'', true).\n%s', ME.message);
end

if opt.MeshFix
    switch computer('arch')
        case 'glnxa64'
            remote_name = 'meshfix.mexa64';
            local_name = remote_name;
        case 'maci64'
            remote_name = 'meshfix.mexmaci64';
            local_name = remote_name;
        case 'maca64'
            remote_name = 'meshfix.mexmaca64';
            local_name = remote_name;
        case 'win64'
            remote_name = 'meshfix_x86-64.exe';
            local_name = 'meshfix.exe';
        otherwise
            error('setup_remeshing:platform', 'No MeshFix download is configured for %s.', computer('arch'));
    end
    bin_dir = fullfile(root, 'code', 'iso2mesh', 'bin');
    if ~isfolder(bin_dir), mkdir(bin_dir); end
    binary = fullfile(bin_dir, local_name);
    if ~isfile(binary)
        if ~opt.DownloadMeshFix
            error('setup_remeshing:meshfix', ...
                'MeshFix is missing: %s. Run setup_remeshing with internet access or copy it there manually.', binary);
        end
        revision = '4a0ca5b65d5d292b83b40fd0fdcb742625e573a6';
        url = ['https://raw.githubusercontent.com/fangq/iso2mesh/' revision '/bin/' remote_name];
        fprintf('Downloading MeshFix from %s\n', url);
        temporary = tempname(bin_dir);
        try
            websave(temporary, url, weboptions('Timeout', 120));
            movefile(temporary, binary);
        catch ME
            if isfile(temporary), delete(temporary); end
            rethrow(ME);
        end
    end
    if isunix
        [ok, message] = fileattrib(binary, '+x', 'u');
        if ~ok, error('setup_remeshing:permissions', '%s', message); end
    end
    fprintf('MeshFix: %s\n', binary);
end
fprintf('Voxelizer check passed. Remeshing files are ready for this MATLAB session.\n');
end
