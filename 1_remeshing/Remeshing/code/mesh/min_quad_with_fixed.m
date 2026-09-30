function [Z,F,Lambda,Lambda_known] = min_quad_with_fixed(A,B,known,Y,Aeq,Beq,F)

  if nargin < 4
    Y = [];
    known = [];
  end
  if nargin < 6
    Aeq = [];
    Beq = [];
  end

  if isempty(Beq)
    Beq = zeros(size(Aeq,1),1);
  end
  if nargin < 7
    F = [];
  end

  if isempty(F) || ~isfield(F,'precomputed') || F.precomputed == false

    F = precompute(A,known,Aeq,F);
  end
  [Z,Lambda,Lambda_known] = solve(F,B,Y,Beq);

  function F = precompute(A,known,Aeq,F)

    n = size(A,1);

    F.n = n;

    if isempty(Aeq)
      Aeq = zeros(0,n);
    end

    assert(size(A,1) == n, ...
      'Rows of system matrix (%d) != problem size (%d)',size(A,1),n);
    assert(size(A,2) == n, ...
      'Columns of system matrix (%d) != problem size (%d)',size(A,2),n);
    assert(isempty(known) || min(size(known))==1, ...
      'known indices (size: %d %d) not a 1D list',size(known));
    assert(isempty(known) || min(known) >= 1, ...
      'known indices (%d) < 1',min(known));
    assert(isempty(known) || max(known) <= n, ...
      'known indices (%d) > problem size (%d)',max(known),n);
    assert(n == size(Aeq,2), ...
      'Columns of linear constraints (%d) != problem size (%d)',size(Aeq,2),n);

    F.known = known;

    F.unknown = find(~sparse(1,known,true,1,n));

    Auu = A(F.unknown,F.unknown);

    F.Ak = A(F.known,:);

    sym_measure = max(max(abs(Auu - Auu')))/max(max(abs(Auu)));

    if sym_measure > eps

      F.Auu_sym = false;
    elseif sym_measure > 0

      F.Auu_sym = true;
    else

      assert(isempty(sym_measure) || sym_measure == 0 || max(max(abs(Auu))) == 0,'not symmetric');

      F.Auu_sym = true;
    end

    F.blank_eq = ~any(Aeq(:,F.unknown),2);
    if any(F.blank_eq)
      warning('min_quad_with_fixed:blank_eq', [ ...
        'Removing blank constraints. ' ...
        'You ought to verify that known values satisfy contsraints']);
      Aeq = Aeq(~F.blank_eq,:);
    end

    neq = size(Aeq,1);

    F.Auu_pd = false;
    if F.Auu_sym && neq == 0

      if issparse(Auu)
        [F.L,p,F.S] = chol(Auu,'lower');
      else
        [F.L,p] = chol(Auu,'lower');
        F.S = eye(size(F.L));
      end
      F.Auu_pd = p==0;
    end

    A_sparse = issparse(A);

    if neq > 1 && ~(isfield(F,'force_Aeq_li') && ~isempty(F.force_Aeq_li)&& F.force_Aeq_li)

      [AeqTQ,AeqTR,AeqTE] = qr(Aeq(:,F.unknown)');
      nc = find(any(AeqTR,2),1,'last');
      if isempty(nc)
        nc = 0;
      end

      assert(nc<=neq);
      F.Aeq_li = nc == neq;
    else
      F.Aeq_li = true;
    end
    if neq > 0 && isfield(F,'force_Aeq_li') && ~isempty(F.force_Aeq_li)
      F.Aeq_li = F.force_Aeq_li;
    end

    if F.Aeq_li

      F.lagrange = n+(1:neq);
      if neq > 0
        if issparse(A) && ~issparse(Aeq)
          warning('min_quad_with_fixed:sparse_system_dense_constraints', ...
          'System is sparse but constraints are not, solve will be dense');
        end
        if issparse(Aeq) && ~issparse(A)
          warning('min_quad_with_fixed:dense_system_sparse_constraints', ...
          'Constraints are sparse but system is not, solve will be dense');
        end
        Z = sparse(neq,neq);

        A = [A Aeq';Aeq Z];

      end

      F.preY = A([F.unknown F.lagrange],known) + ...
        A(known,[F.unknown F.lagrange])';

      F.ldl = false;

      if F.Auu_sym
        if neq == 0 && F.Auu_pd

          F.U = F.L';
          F.P = F.S';
          F.Q = F.S;
        else

          NA = A([F.unknown F.lagrange],[F.unknown F.lagrange]);
          assert(issparse(NA));
          [F.L,F.D,F.P,F.S] = ldl(NA);
          F.ldl = true;
        end
      else
        NA = A([F.unknown F.lagrange],[F.unknown F.lagrange]);

        if issparse(NA)
          [F.L,F.U,F.P,F.Q] = lu(NA);
        else
          [F.L,F.U] = lu(NA);
          F.P = 1;
          F.Q = 1;
        end
      end
    else

      AeqTQ1 = AeqTQ(:,1:nc);
      AeqTR1 = AeqTR(1:nc,:);

      AeqTQ2 = AeqTQ(:,(nc+1):end);
      QRAuu =  AeqTQ2' * Auu * AeqTQ2;

      F.preY = A(F.unknown,known) + A(known,F.unknown)';

      [F.L,p,F.S] = chol(QRAuu,'lower');
      F.U = F.L';
      F.P = F.S';
      F.Q = F.S;

      assert(p==0);

      F.Aeq = Aeq;
      F.AeqTQ2 = AeqTQ2;
      F.AeqTQ1 = AeqTQ1;
      F.AeqTR1 = AeqTR1;
      F.AeqTE = AeqTE;
      F.Auu = Auu;
    end
    F.precomputed = true;
  end

  function [Z,Lambda,Lambda_known] = solve(F,B,Y,Beq)

    kr = numel(F.known);
    if kr == 0
      assert(isempty(Y),'Known values should not be empty');

      if size(Y,2) == 0
        Y = zeros(0,1);
      end
    end
    assert(kr == size(Y,1), ...
      'Number of knowns (%d) != rows in known values (%d)',kr, size(Y,1));
    if isempty(Y)

      if isempty(B)
        if isempty(Beq)
          cols = 1;
          Beq = zeros(0,cols);
        else
          cols = size(Beq,2);
        end
        B = zeros(F.n,cols);
      else
        cols = size(B,2);
      end
      Y = zeros(0,cols);
    else
      cols = size(Y,2);
      if isempty(B)
        B = zeros(F.n,cols);
      end
    end

    if any(F.blank_eq)
      Beq = Beq(~F.blank_eq,:);
    end

    if F.Aeq_li

      neq = numel(F.lagrange);
      if neq == 0
        assert(isempty(Beq),'Constraint right-hand sides should not be empty');
        Beq = zeros(0,1);
      end

      NB = ...
        bsxfun(@plus, ...
          bsxfun(@plus,  ...
            F.preY * Y,  ...
            [B(F.unknown,:); zeros(numel(F.lagrange),size(B,2))]), ...
          [zeros(numel(F.unknown),size(Beq,2)); -2*Beq(F.lagrange-F.n,:)]);

      Z = zeros(F.n+neq,cols);
      Z(F.known,:) = Y;

      if F.ldl
        Z([F.unknown F.lagrange],:) = ...
          -0.5 * F.S * (F.P * (F.L'\(F.D\(F.L\(F.P' * (F.S * NB))))));
      else
        Z([F.unknown F.lagrange],:) = -0.5 * F.Q * (F.U \ (F.L \ ( F.P * NB)));
      end

      Lambda = zeros(numel(F.blank_eq),cols);
      if neq ~= 0

        Lambda(~F.blank_eq,:) = Z(F.lagrange,:);

        Z = Z(1:(end-neq),:);
      end
    else

      Beq = -F.Aeq(:,known)*Y + Beq;

      NB = -0.5*(B(F.unknown,:) + F.preY * Y);
      eff_Beq = F.AeqTE' * Beq;

      AeqTR1T = F.AeqTR1';
      AeqTR1T = AeqTR1T(1:size(F.AeqTQ1,2),1:size(F.AeqTQ1,2));
      eff_Beq = eff_Beq(1:size(F.AeqTQ1,2));
      lambda_0 = F.AeqTQ1 * (AeqTR1T \ eff_Beq);
      QRB = -F.AeqTQ2' * (F.Auu * lambda_0) + F.AeqTQ2' * NB;
      lambda = F.Q * (F.U \ (F.L \ ( F.P * QRB)));

      Z = zeros(F.n,cols);
      Z(F.known,:) = Y;
      Z(F.unknown) = F.AeqTQ2 * lambda + lambda_0;
      Aequ = F.Aeq(:,F.unknown);

      Lambda = F.AeqTE * [ ...
        (F.AeqTR1(:,1:size(F.AeqTR1,1)) \ ...
          (F.AeqTQ1' * NB - F.AeqTQ1' * F.Auu * Z(F.unknown))); ...
        zeros(size(F.AeqTE,2)-size(F.AeqTR1,1),1)
        ];
    end

    Lambda_known = -bsxfun(@plus,F.Ak * Z,0.5*B(F.known,:));
  end

end
