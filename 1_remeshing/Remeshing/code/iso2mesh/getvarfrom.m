function p=getvarfrom(ws,name)

wsname=ws;
if(~iscell(ws))
   wsname=cell(1);
   wsname{1}=ws;
end

p=[];
for i=1:length(wsname)
    isdefined=evalin(wsname{i},['exist(''' name ''')']);
    if(isdefined==1)
        p=evalin(wsname{i},name);
        break;
    end
end
