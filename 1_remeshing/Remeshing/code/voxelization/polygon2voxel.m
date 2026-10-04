function [Volume,FVcent,trans,scaling,offset]=polygon2voxel(FV,VolumeSize,mode,Yxz,hollow)

if ~exist('hollow','var')
    hollow = false;
end

if(nargin<4), Yxz=true; end

if(length(VolumeSize)==1)
    VolumeSize=[VolumeSize VolumeSize VolumeSize];
end
if(length(VolumeSize)~=3)
    error('polygon2voxel:inputs','VolumeSize must be a array of 3 elements ')
end

VolumeSize=round(VolumeSize);

sizev=size(FV.vertices);

if((sizev(2)~=3)||(length(sizev)~=2))
    error('polygon2voxel:inputs','The vertice list is not a m x 3 array')
end

sizef=size(FV.faces);

if((sizef(2)~=3)||(length(sizef)~=2))
    error('polygon2voxel:inputs','The vertice list is not a m x 3 array')
end

if(max(FV.faces(:))>size(FV.vertices,1))
    error('polygon2voxel:inputs','The face list contains an undefined vertex index')
end

if(min(FV.faces(:))<1)
    error('polygon2voxel:inputs','The face list contains an vertex index smaller then 1')
end

if(Yxz)
    FV.vertices=FV.vertices(:,[2 1 3]);
end

switch(lower(mode(1:2)))
    case {'au'}

        trans = min(FV.vertices,[],1);
        FV.vertices=bsxfun(@minus, FV.vertices, trans);
        scaling=min((VolumeSize-1)./(max(FV.vertices(:))));

        FV.vertices=FV.vertices*scaling+1;
        offset = VolumeSize ./ 2 - max(FV.vertices) ./ 2 ;
        FV.vertices = bsxfun(@plus, FV.vertices, offset);
        Wrap=0;
        FVcent = FV;
    case {'ce'}

        FV.vertices=FV.vertices+repmat((VolumeSize/2),size(FV.vertices,1),1);
        Wrap=0;
    case {'wr'}
        Wrap=1;
    case{'cl'}
        Wrap=2;
    otherwise
        Wrap=0;
end

FacesA=double(FV.faces(:,1));
FacesB=double(FV.faces(:,2));
FacesC=double(FV.faces(:,3));
VerticesX=double(FV.vertices(:,1));
VerticesY=double(FV.vertices(:,2));
VerticesZ=double(FV.vertices(:,3));

VolumeSize=double(VolumeSize);

Volume=polygon2voxel_double(FacesA,FacesB,FacesC,VerticesX,VerticesY,VerticesZ,VolumeSize,Wrap);

if ~hollow
    Volume = imfill(Volume,'holes');
end
