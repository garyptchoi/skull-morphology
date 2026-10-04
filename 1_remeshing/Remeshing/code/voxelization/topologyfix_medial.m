function [k_fin,face_common,vert_common,vert_idx,face_fin,vert_fin,type_mod]=topologyfix_medial(Volume,face,vert,vert_idxn,k,genus)

skel=Skeleton3D(Volume);

idx=find(skel(:));
[X,Y,Z]=ind2sub(size(skel),idx);
Points=[X,Y,Z];
D1 = squareform(pdist(X));
D2 = squareform(pdist(Y));
D3 = squareform(pdist(Z));

Adj = sparse(D1<2 & D2<2 & D3<2 )-speye(size(D1,1));

if exist('graphconncomp') ~= 0
    [S, C] = graphconncomp(Adj);
else
    C = conncomp(graph(Adj));
    S = length(unique(C));
end
Points_temp=Points;
Adj_temp=Adj;
if S~=1
    idxx=histc(C,1:S);
    [~,idxx]=max(idxx);
    idxx=C==idxx;
    Points_temp=Points_temp(idxx,:);
    Adj_temp=Adj_temp(idxx,idxx);

end

while true
    deg=sum(Adj_temp);
    idx= deg==1;
    if sum(idx)==0
        break;
    end
    Points_temp=Points_temp(~idx,:);
    Adj_temp=Adj_temp(~idx,~idx);
end

Adj_sym = Adj_temp + Adj_temp';
Adj_sym(Adj_sym > 1) = 1;

G_obj = graph(Adj_sym);

cycles_all = cyclebasis(G_obj);

cellsz = cellfun('length',cycles_all);
[val_sz,idx]=sort(cellsz);
cycles_all=cycles_all(idx);
cycles_all=cycles_all(val_sz>3);

Volume_topology=cell(length(cycles_all),1);

for pp=1:length(cycles_all)
    Points_cycles=Points_temp(cycles_all{pp},:);

    k_cycle = alphaShape(Points_cycles);

    if isinf(k_cycle.Alpha)
        rand_idx=randperm(size(Points_cycles,1));
        rand_idx=rand_idx(1:3);
        P_plane=Points_cycles(rand_idx,:);
        normal_p=cross(P_plane(1,:)-P_plane(3,:),P_plane(3,:)-P_plane(2,:));
        if sum(abs(normal_p))==0
            Points_cycles_inc=mean(Points_cycles)+rand(1,3);
            k_cycle = alphaShape([Points_cycles;Points_cycles_inc]);
        else
            d_plane=-sum((repmat(normal_p,size(Points_cycles,1),1).*Points_cycles),2);
            if length(numel(unique(d_plane)))==1
                Points_cycles_inc=mean(Points_cycles)+rand(1,3);
                k_cycle = alphaShape([Points_cycles;Points_cycles_inc]);
            end

        end
    end

    [face_cy,vert_cy] = boundaryFacets(k_cycle);

    FV_cy.faces = face_cy;
    FV_cy.vertices = vert_cy;

    Volume_temp=polygon2voxel(FV_cy,size(Volume),'none');
    idx=find(Volume_temp(:));
    [X_cy,Y_cy,Z_cy]=ind2sub(size(Volume),idx);
    Points_fillcy=[X_cy,Y_cy,Z_cy];
    tf_cy = inShape(k,X_cy,Y_cy,Z_cy);
    Points_fillcy=Points_fillcy(~tf_cy,:);
    if size(Points_fillcy,1)>0
        ind_cycle=sub2ind(size(Volume),Points_fillcy(:,1),Points_fillcy(:,2),Points_fillcy(:,3));
        Volume_top=false(size(Volume));
        Volume_top(ind_cycle)=1;
        Volume_top=perturb_volume_same_min(Volume_top,1);
        Volume_top=imfill(Volume_top,'holes');
        Volume_top = permute(Volume_top,[2 1 3]);
        Volume_topology{pp}=Volume_top;
    else
        Volume_topology{pp}=[];
    end

end

Volume_new=Volume;
genus_new=genus;
for pp=1:length(Volume_topology)

    if ~isempty(Volume_topology{pp})
        Volume_temp=Volume_new;
        genus_temp=genus_new;
        Volume_new=(Volume_new+Volume_topology{pp})>0;
        idx=find(Volume_new(:));
        [X_t,Y_t,Z_t]=ind2sub(size(Volume_new),idx);
        k_top = alphaShape([X_t,Y_t,Z_t]);
        [face_t,vert_t] = boundaryFacets(k_top);
        genus_new=calc_genus(vert_t,face_t);

        if genus_new>=genus_temp
            Volume_new=Volume_temp;
            genus_new=genus_temp;
            continue;
        end

        if genus_new<genus_temp && genus_new>=0

            Volume_top=imfill(Volume_new,'holes');
            idx_new=find(Volume_top(:));

            if length(idx_new)-length(idx)~=0
                Volume_new=Volume_temp;
                genus_new=genus_temp;
                continue;
            end
        elseif genus_new<genus_temp  && genus_new<0
            Volume_new=Volume_temp;
            genus_new=genus_temp;
            continue;
        end
        if genus_new ==0
            k_fin=k_top;
            face_fin=face_t;
            vert_fin=vert_t;
            break;
        end
    end
end

alter=0;
if genus_new~=0
    alter=1;
    Volume_int=Volume_new;
    genus_alt=genus_new;
    Volume_new=perturb_volume_same_min(Volume_new,1);
    Volume_new=imfill(Volume_new,'holes');
    idx=find(Volume_new(:));
    [X_t,Y_t,Z_t]=ind2sub(size(Volume_new),idx);
    k_top = alphaShape([X_t,Y_t,Z_t]);
    [face_t,vert_t] = boundaryFacets(k_top);
    genus_new=calc_genus(vert_t,face_t);
    if genus_new>=genus_alt
        Volume_new=Volume_int;
        alter=0;
    end

    if genus_new==0
        k_fin=k_top;
        face_fin=face_t;
        vert_fin=vert_t;
    end
end

iter=1;
iternum=100;
per=1.05;

while_alter=0;
while genus_new~=0  && iter<iternum

    k_top = alphaShape([X_t,Y_t,Z_t],per*(max(k_top.Alpha,1)));
    [face_t,vert_t] = boundaryFacets(k_top);
    genus_new=calc_genus(vert_t,face_t);

    k_fin=k_top;
    face_fin=face_t;
    vert_fin=vert_t;
    while_alter=1;

    iter=iter+1;
end

V_top = volume(k_fin);

iter=1;
iternum=100;
per=1.05;
idx=find(Volume(:));
k_dir=k;
[X,Y,Z]=ind2sub(size(Volume),idx);
genus_dir=genus;
while genus_dir~=0  && iter<iternum

    k_dir= alphaShape([X,Y,Z],per*(max(k_dir.Alpha,1)));
    [face_dir,vert_dir] = boundaryFacets(k_dir);
    genus_dir=calc_genus(vert_dir,face_dir);
    iter=iter+1;
end

V_dir=volume(k_dir);

while_direct=0;
if V_dir<V_top
    k_fin=k_dir;
    face_fin=face_dir;
    vert_fin=vert_dir;
    while_direct=1;
    while_alter=0;
    alter=0;
end

vert_mat=[vert;vert_fin];
[C,~,icv] = unique(vert_mat,'rows');
vert_idx=ismember(vert_fin,vert(vert_idxn,:),'rows');
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

type_mod=[while_direct,alter,while_alter];
end
