function skel = Skeleton3D(img,spare)

disp('computing medial axis............................');

skel=padarray(img,[1 1 1]);

if(nargin==2)
    spare=padarray(spare,[1 1 1]);
end;

l_orig = length(find(skel(:)));

eulerLUT = FillEulerLUT;

iter = 1;

global width height depth

width = size(skel,1);
height = size(skel,2);
depth = size(skel,3);

unchangedBorders = 0;

while( unchangedBorders < 6 )
    unchangedBorders = 0;
    for currentBorder=1:6
        cands=zeros(width,height,depth);
        switch currentBorder
            case 4,
                x=2:size(skel,1);
                cands(x,:,:)=skel(x,:,:) - skel(x-1,:,:);
            case 3,
                x=1:size(skel,1)-1;
                cands(x,:,:)=skel(x,:,:) - skel(x+1,:,:);
            case 1,
                y=2:size(skel,2);
                cands(:,y,:)=skel(:,y,:) - skel(:,y-1,:);
            case 2,
                y=1:size(skel,2)-1;
                cands(:,y,:)=skel(:,y,:) - skel(:,y+1,:);
            case 6,
                z=2:size(skel,3);
                cands(:,:,z)=skel(:,:,z) - skel(:,:,z-1);
            case 5,
                z=1:size(skel,3)-1;
                cands(:,:,z)=skel(:,:,z) - skel(:,:,z+1);
        end;

        if(nargin==2)
            cands = cands.*~spare;
        end;

        cands = intersect(find(cands(:)==1),find(skel(:)==1));

        noChange = true;

        if(~isempty(cands))

            [x y z]=ind2sub([width height depth],cands);

            nhood = logical(pk_get_nh(skel,cands));

            di1 = find(sum(nhood,2)==2);
            nhood(di1,:)=[];
            cands(di1)=[];
            x(di1)=[];
            y(di1)=[];
            z(di1)=[];

            di2 = find(~p_EulerInv(nhood, eulerLUT'));
            nhood(di2,:)=[];
            cands(di2)=[];
            x(di2)=[];
            y(di2)=[];
            z(di2)=[];

            di3 = find(~p_is_simple(nhood));
            nhood(di3,:)=[];
            cands(di3)=[];
            x(di3)=[];
            y(di3)=[];
            z(di3)=[];

            if(~isempty(x))
                x1 = find(mod(x,2));
                x2 = find(~mod(x,2));
                y1 = find(mod(y,2));
                y2 = find(~mod(y,2));
                z1 = find(mod(z,2));
                z2 = find(~mod(z,2));
                ilst(1).l = intersect(x1,intersect(y1,z1));
                ilst(2).l = intersect(x2,intersect(y1,z1));
                ilst(3).l = intersect(x1,intersect(y2,z1));
                ilst(4).l = intersect(x2,intersect(y2,z1));
                ilst(5).l = intersect(x1,intersect(y1,z2));
                ilst(6).l = intersect(x2,intersect(y1,z2));
                ilst(7).l = intersect(x1,intersect(y2,z2));
                ilst(8).l = intersect(x2,intersect(y2,z2));

                idx = [];

                for i = 1:8
                    if(~isempty(ilst(i).l))
                        idx = ilst(i).l;
                        li = sub2ind([width height depth],x(idx),y(idx),z(idx));
                        skel(li)=0;
                        nh = logical(pk_get_nh(skel,li));
                        di_rc = find(~p_is_simple(nh));
                        if(~isempty(di_rc))
                            skel(li(di_rc))=1;
                        else
                            noChange = false;
                        end;
                    end;
                end;
            end;
        end;

        if( noChange )
            unchangedBorders = unchangedBorders + 1;
        end;
        fprintf('\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b');
        fprintf('removed %3d%% voxels',round(100*(l_orig-length(find(skel(:))))/l_orig));

    end;
end;

fprintf('\n');

skel = skel(2:end-1,2:end-1,2:end-1);
