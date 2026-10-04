function [no,el]=removeisolatednode(node,elem)

oid=1:size(node,1);
if(~iscell(elem))
    idx=setdiff(oid,elem(:));
else
    el=cell2mat(elem);
    idx=setdiff(oid,el(:));
end
idx=sort(idx);
delta=zeros(size(oid));
delta(idx)=1;
delta=-cumsum(delta);
oid=oid+delta;
if(~iscell(elem))
    el=oid(elem);
else
    el=cellfun(@(x) oid(x), elem,'UniformOutput',false);
end
no=node;
no(idx,:)=[];
