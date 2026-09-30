function Volume_perturb=perturb_volume_same_min(Volume,more_conn)

if ~more_conn
    [sx,sy,sz]=size(Volume);
    Volume_perturb=false(sx+2,sy+2,sz+2);
    Volume_perturb_temp=false(sx+2,sy+2,sz+2);

    Volume_perturb(2:sx+1,2:sy+1,2:sz+1)=Volume;

    Volume_perturb_temp(1:sx,2:sy+1,2:sz+1)=Volume;
    Volume_perturb=Volume_perturb_temp|Volume_perturb;
    Volume_perturb_temp(3:sx+2,2:sy+1,2:sz+1)=Volume;
    Volume_perturb=Volume_perturb_temp|Volume_perturb;

    Volume_perturb_temp(2:sx+1,1:sy,2:sz+1)=Volume;
    Volume_perturb=Volume_perturb_temp|Volume_perturb;
    Volume_perturb_temp(2:sx+1,3:sy+2,2:sz+1)=Volume;
    Volume_perturb=Volume_perturb_temp|Volume_perturb;

    Volume_perturb_temp(2:sx+1,2:sy+1,1:sz)=Volume;
    Volume_perturb=Volume_perturb_temp|Volume_perturb;
    Volume_perturb_temp(2:sx+1,2:sy+1,3:sz+2)=Volume;
    Volume_perturb=Volume_perturb_temp|Volume_perturb;
elseif more_conn
    B=ones(2,2,2);
    Volume_perturb= convn(Volume,B,'same');
    Volume_perturb= Volume_perturb>0;

end

end
