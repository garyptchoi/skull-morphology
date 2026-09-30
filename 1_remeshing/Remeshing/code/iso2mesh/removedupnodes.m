function [newnode,newelem]=removedupnodes(node,elem,tol)

if(nargin>=3 && tol~=0)
    node=round(node/tol)*tol;
end
[newnode,I,J]=unique(node,'rows');
if(iscell(elem))
    newelem=cellfun(@(x) J(x)', elem,'UniformOutput',false);
else
    newelem=J(elem);
end
