function [v, f, n, name] = stlReadAscii(fileName)

fid = fopen(fileName);
cellcontent = textscan(fid,'%s','delimiter','\n');
content = cellcontent{:}(logical(~strcmp(cellcontent{:},'')));
fclose(fid);

line1 = char(content(1));
if (size(line1,2) >= 7)
    name = line1(7:end);
else
    name = 'Unnamed Object';
end

normals = char(content(logical(strncmp(content,'facet normal',12))));
n = str2num(normals(:,13:end));

vertices = char(content(logical(strncmp(content,'vertex',6))));
v = str2num(vertices(:,7:end));
nvert = size(vertices,1);
nfaces = sum(strcmp(content,'endfacet'));
if (nvert == 3*nfaces)
    f = reshape(1:nvert,[3 nfaces])';
end

[v,f] = stlSlimVerts(v,f);
