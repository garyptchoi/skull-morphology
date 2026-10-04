function [v, f, n, name] = stlReadBinary(fileName)

fid = fopen(fileName);
header = fread(fid,80,'int8');
name = deblank(native2unicode(header,'ascii')');
if isempty(name)
    name = 'Unnamed Object';
end
nfaces = fread(fid,1,'int32');
nvert = 3*nfaces;

n = zeros(nfaces,3);
v = zeros(nvert,3);
f = zeros(nfaces,3);
for i = 1 : nfaces
    tmp = fread(fid,3*4,'float');
    n(i,:) = tmp(1:3);
    v(3*i-2,:) = tmp(4:6);
    v(3*i-1,:) = tmp(7:9);
    v(3*i,:) = tmp(10:12);
    f(i,:) = [3*i-2 3*i-1 3*i];
    fread(fid,1,'int16');
end
fclose(fid);

[v,f] = stlSlimVerts(v,f);
