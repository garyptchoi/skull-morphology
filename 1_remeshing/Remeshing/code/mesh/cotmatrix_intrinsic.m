function [L,cot] = cotmatrix_intrinsic(l,F,nvert)

  if(size(F,1) == 3)
    warning('F seems to be 3 by #F, it should be #F by 3');
  end
  F = F';

  i1 = F(1,:); i2 = F(2,:); i3 = F(3,:);
  l1 = l(:,1); l2 = l(:,2); l3 = l(:,3);

  s = (l1 + l2 + l3)*0.5;

  dblA = real(2*sqrt( s.*(s-l1).*(s-l2).*(s-l3)))+1e-6;

  cot12 = (l1.^2 + l2.^2 -l3.^2)./dblA/4;
  cot23 = (l2.^2 + l3.^2 -l1.^2)./dblA/4;
  cot31 = (l1.^2 + l3.^2 -l2.^2)./dblA/4;

  diag1 = -cot12-cot31; diag2 = -cot12-cot23; diag3 = -cot31-cot23;

  i = [i1 i2 i2 i3 i3 i1  i1 i2 i3];
  j = [i2 i1 i3 i2 i1 i3  i1 i2 i3];

  v = [cot12 cot12 cot23 cot23 cot31 cot31 diag1 diag2 diag3];

  L = sparse(i,j,v,nvert,nvert);
  cot=[cot12,cot23,cot31];
end
