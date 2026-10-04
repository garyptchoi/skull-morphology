function format = stlGetFormat(fileName)

fid = fopen(fileName);

fseek(fid,0,1);
fidSIZE = ftell(fid);
if rem(fidSIZE-84,50) > 0
    format = 'ascii';
else

    fseek(fid,0,-1);
    header = strtrim(char(fread(fid,80,'uchar')'));
    isSolid = strcmp(header(1:min(5,length(header))),'solid');
    fseek(fid,-80,1);
    tail = char(fread(fid,80,'uchar')');
    isEndSolid = findstr(tail,'endsolid');

    if isSolid & isEndSolid
        format = 'ascii';
    else
        format = 'binary';
    end
end
fclose(fid);
