function saveoff(v,f,fname)

fid=fopen(fname,'wt');
if(fid==-1)
    error('You do not have permission to save mesh files.');
end
fprintf(fid,'OFF\n');
fprintf(fid,'%d\t%d\t%d\n',length(v),length(f),0);
fprintf(fid,'%.16f\t%.16f\t%.16f\n',v');
face=[size(f,2)*ones(size(f,1),1) f-1];
format=[repmat('%d\t',1,size(face,2)-1) '%d\n'];
fprintf(fid,format,face');
fclose(fid);
