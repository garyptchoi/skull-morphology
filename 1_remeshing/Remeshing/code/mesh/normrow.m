function [ B ] = normrow( A )

  switch size(A,2)
  case 2
    B = hypot(A(:,1),A(:,2));
  otherwise
    B = sqrt(sum(A.^2,2));
  end
end
