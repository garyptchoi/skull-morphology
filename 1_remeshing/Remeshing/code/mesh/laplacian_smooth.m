function [U,Uall] = laplacian_smooth(V,F,L_method,b,lambda,method,S,max_iter)

  n = size(V,1);

  dim = size(V,2);

  if(~exist('L_method','var'))
    L_method = 'cotan';
  end

  if(~exist('lambda','var'))
    lambda = 0.1;
  end

  if(~exist('b','var'))
    b = [];
  end

  I = speye(n,n);

  if(~exist('method','var'))
    method = 'implicit';
  end

  h = avgedge(V,F);
  if(~exist('tol','var'))
    tol = 0.001;
  end

  if(~exist('max_iter','var'))
    max_iter = 1000;
  end

  if(~exist('S','var'))
    S = V;
  end

  if strcmp(L_method,'uniform')

    A = adjacency_matrix(F);
    L = A - diag(sum(A));
  end

  P = [];
  sym = [];

  iter = 0;
  U = S;
  U_prev = S;
  if nargout >= 2
    Uall = [];
  end

  if strcmp(L_method,'cotan')

    L = cotmatrix_embedded(V,F);

  end

  while( iter < max_iter && (iter == 0 || max(abs(U(:)-U_prev(:)))>tol*h))
    U_prev = U;
    switch method
    case 'implicit'
      Q = (I-lambda*L);

      for d = 1:size(S,2)
        [U(:,d),P] = min_quad_with_fixed(Q*0.5,-U(:,d),b,S(b,d),[],[],P);
      end
    case 'explicit'
      Q = (I+lambda*L);
      U = Q * U;

      U(b,:) = S(b,:);
    otherwise
      error(['' method ' is not a supported smoothing method']);
    end

    if nargout >= 2
      Uall = cat(3,Uall,U);
    end
    iter = iter + 1;
  end

end
