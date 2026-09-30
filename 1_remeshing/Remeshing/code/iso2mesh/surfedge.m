function [openedge,elemid]=surfedge(f,varargin)

if(isempty(f))
    openedge=[];
    return;
end

opt=varargin2struct(varargin{:});
findjunc=jsonopt('Junction',0,opt);

if(size(f,2)==3)
    edges=[f(:,[1,2]);
           f(:,[2,3]);
           f(:,[3,1])];
elseif(size(f,2)==4)
    edges=[f(:,[1,2,3]);
           f(:,[2,1,4]);
           f(:,[1,3,4]);
           f(:,[2,4,3])];
else
    error('surfedge only supports 2D and 3D elements');
end

edgesort=sort(edges,2);
[foo,ix,jx]=unique(edgesort,'rows');

if(isoctavemesh)
        u=unique(jx);
        if(size(f,2)==3 && findjunc)
            qx=u(hist(jx,u)>2);
        else
	    qx=u(hist(jx,u)==1);
        end
else
	vec=histc(jx,1:max(jx));
        if(size(f,2)==3 && findjunc)
            qx=find(vec>2);
        else
	    qx=find(vec==1);
        end
end
openedge=edges(ix(qx),:);
if(nargout>=2)
    [elemid, iy]=ind2sub(size(f),ix(qx));
end
