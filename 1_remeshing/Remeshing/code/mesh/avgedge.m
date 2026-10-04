function [ b ] = avgedge(V,F)

  E = edges(F);
  B = normrow(V(E(:,1),:)-V(E(:,2),:))+1e-10;

  b = mean(B);

end
