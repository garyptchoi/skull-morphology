function E = edges(F)

  n = size(F,2);

  e = nchoosek(1:n,2);
  A = sparse(F(:,e(:,1)),F(:,e(:,2)),1,max(F(:)),max(F(:)));
  [EI,EJ] = find(tril(A+A'));
  E = [EJ EI];

end
