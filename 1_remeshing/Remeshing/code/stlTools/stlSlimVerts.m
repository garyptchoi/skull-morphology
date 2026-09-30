function [vnew, fnew]= stlSlimVerts(v, f)

if ~exist('v','var')
    error('The vertex list (v) must be specified.');
end
if ~exist('f','var')
    error('The vertex connectivity of the triangle faces (f) must be specified.');
end

[vnew, indexm, indexn] =  unique(v, 'rows');
fnew = indexn(f);
