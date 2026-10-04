function [k_final,Points,facen,vertn,vert_idx,genus_fin,k_org,change_gen,vertn_]=voxelelize_genus(vert,face,sizen,connected,perturb)

FV.faces = face;
FV.vertices = vert;

[Volume,FVcent,trans,scaling,offset]=polygon2voxel(FV,[sizen sizen sizen],'auto');

if perturb
Volume=perturb_volume_min_lg(Volume,0);
end
Volume=imfill(Volume,'holes');

if connected
    CC = bwconncomp(Volume,26);
    numPixels = cellfun(@numel,CC.PixelIdxList);
    [~,idx] = max(numPixels);
    idx=CC.PixelIdxList{idx};
    [X,Y,Z]=ind2sub(size(Volume),idx);
    Vol_mod=false(size(Volume));
    Vol_mod(idx)=1;

else
    idx=find(Volume(:));
    [X,Y,Z]=ind2sub(size(Volume),idx);
    Vol_mod=Volume;
end

Points=[X,Y,Z];

k = alphaShape(Points,0.9);
N = numRegions(k);
if N==1
    k_org=k;
    [facen,vertn] = boundaryFacets(k);

    genus=calc_genus(vertn,facen);
else
    k_org=k;
    sz_N=zeros(N,1);
    for pp=1:N
        [~,vertn] = boundaryFacets(k,pp);
        sz_N(pp)=size(vertn,1);
    end
    [~,idx]=max(sz_N);
    [facen,vertn] = boundaryFacets(k,idx);
    tf = inShape(k,Points,idx);
    Points=Points(tf,:);
    k = alphaShape(Points);
    new_idx=sub2ind(size(Volume),Points(:,1),Points(:,2),Points(:,3));
    Vol_mod=false(size(Volume));
    Vol_mod(new_idx)=1;

    genus=calc_genus(vertn,facen);
end

if genus~=0
    change_gen=true;
    [Vol_final, k_final,genus_fin,~,~,vert_idx,facen,vertn,~]=topology_axis_fixtop(Vol_mod,k,genus,vertn,facen);
    if genus_fin~=0
        [k_final,~,~,vert_idx,facen,vertn,~]=topologyfix_medial(Vol_final,facen,vertn,vert_idx,k_final,genus_fin);
    end
else
    change_gen=false;
    k_final=k;
    genus_fin=genus;
    [facen,vertn] = boundaryFacets(k_final);
    vert_idx=true(size(vertn,1),1);
end

vertn_ =  bsxfun(@minus, vertn, offset);
vertn_ = vertn_-1;
vertn_ = vertn_/scaling;
vertn_ = bsxfun(@plus, vertn_, trans);
vertn_=vertn_(:,[2 1 3]);

end
