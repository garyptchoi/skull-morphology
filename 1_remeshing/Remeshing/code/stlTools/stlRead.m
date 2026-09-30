function [v, f, n, name] = stlRead(fileName)

format = stlGetFormat(fileName);
if strcmp(format,'ascii')
  [v,f,n,name] = stlReadAscii(fileName);
elseif strcmp(format,'binary')
  [v,f,n,name] = stlReadBinary(fileName);
end
