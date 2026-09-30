function [A] = adjacency_matrix(E)

  if size(E,2)>2
    F = E;
    E = edges(F);
  end

  A = sparse([E(:,1) E(:,2)],[E(:,2) E(:,1)],1);
end
