function [Vol_final, k_final,genus_fin,vert_common,face_common,vert_idx,face_fin,vert_fin,axis_mod]=topology_axis_fixtop(Volume,k,genus,vert,face)

axis_mod=zeros(3,1);
[sx,sy,sz]=size(Volume);
[X,Y,Z]=ind2sub(size(Volume),find(Volume(:)));
Points=[X,Y,Z];
Points_iter=Points;

genus_x_iter=genus;
pp_index=1:sx;
for xx=1:length(pp_index)
    pp=pp_index(xx);
    region_curr=squeeze(Volume(pp,:,:));
    [B_hole,Lb,Nb,~] = bwboundaries(region_curr);

    idx_accept=zeros(length(B_hole),1);
    for kk=1:length(B_hole)-Nb
        idx=kk+Nb;
        region_temp=Lb==idx;
        [i,j]=find(region_temp);
        Points_add=[pp*ones(length(i),1),i,j;min(sz,(pp+1))*ones(length(i),1),i,j];
        Points_temp=[Points_iter;Points_add];
        kx_temp = alphaShape(Points_temp,k.Alpha);
        [facenx,vertnx] = boundaryFacets(kx_temp);
        genusx_temp=calc_genus(vertnx,facenx);
        Vol_fill=false(size(Volume));
        ind_fill=sub2ind(size(Volume),Points_temp(:,1),Points_temp(:,2),Points_temp(:,3));
        Vol_fill(ind_fill)=1;
        Vol_fill=imfill(Vol_fill,'holes');
        fill_idx=length(ind_fill)-length(find(Vol_fill(:)));

        if genusx_temp<genus_x_iter && fill_idx==0 && genusx_temp>=0

            idx_accept(idx)=1;
            Points_iter=[Points_iter;Points_add];
            genus_x_iter=genusx_temp;
        end
    end
end

if genus_x_iter==0;
    k_final = alphaShape(Points_iter,k.Alpha);
    [face_fin,vert_fin] = boundaryFacets(k_final);
    Vol_final=false(size(Volume));
    ind_final=sub2ind(size(Volume),Points_iter(:,1),Points_iter(:,2),Points_iter(:,3));
    Vol_final(ind_final)=1;
    Vol_final=imfill(Vol_final,'holes');

    axis_mod(1)=1;

    vert_mat=[vert;vert_fin];
    [C,~,icv] = unique(vert_mat,'rows');
    vert_idx=ismember(vert_fin,vert,'rows');
    ic1=icv(1:length(vert));
    vert_s=vert_mat((ic1),:);
    ic2=icv(length(vert)+1:end);
    vert_fins=vert_mat((ic2),:);
    facen_i=ic1(face);
    facen1_i=ic2(face_fin);
    facen_is=sort(facen_i');
    facen_is=facen_is';
    facen1_is=sort(facen1_i');
    facen1_is=facen1_is';

    [~,~,icf] = unique([facen_is;facen1_is],'rows');
    ic1=icf(1:length(facen_is));
    ic2=icf(length(facen_is)+1:end);
    idx_common=ismember(ic2,ic1);
    face_common=facen1_i(idx_common,:);

    [unq_face,~,face_common]=unique(face_common);
    face_common=reshape(face_common,size(face_common,1)/3,3);
    vert_common=C(unq_face,:);

    genus_fin=genus_x_iter;
    return;
end

pp_index=sy:-1:1;
for xx=1:length(pp_index)
    pp=pp_index(xx);
    region_curr=squeeze(Volume(:,pp,:));
    [B_hole,Lb,Nb,~] = bwboundaries(region_curr);

    idx_accept=zeros(length(B_hole),1);
    for kk=1:length(B_hole)-Nb
        idx=kk+Nb;
        region_temp=Lb==idx;
        [i,j]=find(region_temp);
        Points_add=[i,pp*ones(length(i),1),j;i,min(sz,(pp+1))*ones(length(i),1),j];
        Points_temp=[Points_iter;Points_add];
        kx_temp = alphaShape(Points_temp,k.Alpha);
        [facenx,vertnx] = boundaryFacets(kx_temp);
        genusx_temp=calc_genus(vertnx,facenx);
        Vol_fill=false(size(Volume));
        ind_fill=sub2ind(size(Volume),Points_temp(:,1),Points_temp(:,2),Points_temp(:,3));
        Vol_fill(ind_fill)=1;
        Vol_fill=imfill(Vol_fill,'holes');
        fill_idx=length(ind_fill)-length(find(Vol_fill(:)));

        if genusx_temp<genus_x_iter && fill_idx==0 && genusx_temp>=0

            idx_accept(idx)=1;
            Points_iter=[Points_iter;Points_add];
            genus_x_iter=genusx_temp;
        end
    end
end

if genus_x_iter==0;
    k_final = alphaShape(Points_iter,k.Alpha);
    [face_fin,vert_fin] = boundaryFacets(k_final);
    Vol_final=false(size(Volume));
    ind_final=sub2ind(size(Volume),Points_iter(:,1),Points_iter(:,2),Points_iter(:,3));
    Vol_final(ind_final)=1;
    Vol_final=imfill(Vol_final,'holes');
    axis_mod(2)=1;

    vert_mat=[vert;vert_fin];
    [C,~,icv] = unique(vert_mat,'rows');
    vert_idx=ismember(vert_fin,vert,'rows');
    ic1=icv(1:length(vert));
    vert_s=vert_mat((ic1),:);
    ic2=icv(length(vert)+1:end);
    vert_fins=vert_mat((ic2),:);
    facen_i=ic1(face);
    facen1_i=ic2(face_fin);
    facen_is=sort(facen_i');
    facen_is=facen_is';
    facen1_is=sort(facen1_i');
    facen1_is=facen1_is';

    [~,~,icf] = unique([facen_is;facen1_is],'rows');
    ic1=icf(1:length(facen_is));
    ic2=icf(length(facen_is)+1:end);
    idx_common=ismember(ic2,ic1);
    face_common=facen1_i(idx_common,:);

    [unq_face,~,face_common]=unique(face_common);
    face_common=reshape(face_common,size(face_common,1)/3,3);
    vert_common=C(unq_face,:);
    genus_fin=genus_x_iter;
    return;
end

pp_index=1:sz;
for xx=1:length(pp_index)
    pp=pp_index(xx);
    region_curr=squeeze(Volume(:,:,pp));
    [B_hole,Lb,Nb,~] = bwboundaries(region_curr);

    idx_accept=zeros(length(B_hole),1);
    for kk=1:length(B_hole)-Nb
        idx=kk+Nb;
        region_temp=Lb==idx;
        [i,j]=find(region_temp);
        Points_add=[i,j,pp*ones(length(i),1);i,j,min(sz,(pp+1))*ones(length(i),1)];
        Points_temp=[Points_iter;Points_add];
        kx_temp = alphaShape(Points_temp,k.Alpha);
        [facenx,vertnx] = boundaryFacets(kx_temp);
        genusx_temp=calc_genus(vertnx,facenx);
        Vol_fill=false(size(Volume));
        ind_fill=sub2ind(size(Volume),Points_temp(:,1),Points_temp(:,2),Points_temp(:,3));
        Vol_fill(ind_fill)=1;
        Vol_fill=imfill(Vol_fill,'holes');
        fill_idx=length(ind_fill)-length(find(Vol_fill(:)));

        if genusx_temp<genus_x_iter && fill_idx==0 && genusx_temp>=0

            idx_accept(idx)=1;
            Points_iter=[Points_iter;Points_add];
            genus_x_iter=genusx_temp;
        end
    end
end

if genus_x_iter==0;
    k_final = alphaShape(Points_iter,k.Alpha);
    [face_fin,vert_fin] = boundaryFacets(k_final);
    Vol_final=false(size(Volume));
    ind_final=sub2ind(size(Volume),Points_iter(:,1),Points_iter(:,2),Points_iter(:,3));
    Vol_final(ind_final)=1;
    Vol_final=imfill(Vol_final,'holes');
    axis_mod(3)=1;

    vert_mat=[vert;vert_fin];
    [C,~,icv] = unique(vert_mat,'rows');
    vert_idx=ismember(vert_fin,vert,'rows');
    ic1=icv(1:length(vert));
    vert_s=vert_mat((ic1),:);
    ic2=icv(length(vert)+1:end);
    vert_fins=vert_mat((ic2),:);
    facen_i=ic1(face);
    facen1_i=ic2(face_fin);
    facen_is=sort(facen_i');
    facen_is=facen_is';
    facen1_is=sort(facen1_i');
    facen1_is=facen1_is';

    [~,~,icf] = unique([facen_is;facen1_is],'rows');
    ic1=icf(1:length(facen_is));
    ic2=icf(length(facen_is)+1:end);
    idx_common=ismember(ic2,ic1);
    face_common=facen1_i(idx_common,:);

    [unq_face,~,face_common]=unique(face_common);
    face_common=reshape(face_common,size(face_common,1)/3,3);
    vert_common=C(unq_face,:);
    genus_fin=genus_x_iter;
    return;
end

k_final = alphaShape(Points_iter,k.Alpha);
[face_fin,vert_fin] = boundaryFacets(k_final);
Vol_final=false(size(Volume));
ind_final=sub2ind(size(Volume),Points_iter(:,1),Points_iter(:,2),Points_iter(:,3));
Vol_final(ind_final)=1;
Vol_final=imfill(Vol_final,'holes');

vert_mat=[vert;vert_fin];
[C,~,icv] = unique(vert_mat,'rows');
vert_idx=ismember(vert_fin,vert,'rows');
ic1=icv(1:length(vert));
vert_s=vert_mat((ic1),:);
ic2=icv(length(vert)+1:end);
vert_fins=vert_mat((ic2),:);
facen_i=ic1(face);
facen1_i=ic2(face_fin);
facen_is=sort(facen_i');
facen_is=facen_is';
facen1_is=sort(facen1_i');
facen1_is=facen1_is';

[~,~,icf] = unique([facen_is;facen1_is],'rows');
ic1=icf(1:length(facen_is));
ic2=icf(length(facen_is)+1:end);
idx_common=ismember(ic2,ic1);
face_common=facen1_i(idx_common,:);

[unq_face,~,face_common]=unique(face_common);
face_common=reshape(face_common,size(face_common,1)/3,3);
vert_common=C(unq_face,:);

genus_fin=genus_x_iter;
end
