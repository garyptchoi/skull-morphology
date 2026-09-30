function [TR, TT, ER, t] = icp_matlabcentral(q,p,varargin)

inp = inputParser;
inp.addRequired('q', @(x)isreal(x) && size(x,1) == 3);
inp.addRequired('p', @(x)isreal(x) && size(x,1) == 3);
inp.addOptional('iter', 10, @(x)x > 0 && x < 10^5);
inp.addParamValue('Boundary', [], @(x)size(x,1) == 1);
inp.addParamValue('EdgeRejection', false, @(x)islogical(x));
inp.addParamValue('Extrapolation', false, @(x)islogical(x));
validMatching = {'bruteForce','Delaunay','kDtree'};
inp.addParamValue('Matching', 'bruteForce', @(x)any(strcmpi(x,validMatching)));
validMinimize = {'point','plane','lmapoint'};
inp.addParamValue('Minimize', 'point', @(x)any(strcmpi(x,validMinimize)));
inp.addParamValue('Normals', [], @(x)isreal(x) && size(x,1) == 3);
inp.addParamValue('NormalsData', [], @(x)isreal(x) && size(x,1) == 3);
inp.addParamValue('ReturnAll', false, @(x)islogical(x));
inp.addParamValue('Triangulation', [], @(x)isreal(x) && size(x,2) == 3);
inp.addParamValue('Verbose', false, @(x)islogical(x));
inp.addParamValue('Weight', @(x)ones(1,length(x)), @(x)isa(x,'function_handle'));
inp.addParamValue('WorstRejection', 0, @(x)isscalar(x) && x > 0 && x < 1);
inp.parse(q,p,varargin{:});
arg = inp.Results;
clear('inp');

t = zeros(arg.iter+1,1);

tic;
Np = size(p,2);

pt = p;

ER = zeros(arg.iter+1,1);

T = zeros(3,1);
R = eye(3,3);

TT = zeros(3,1, arg.iter+1);
TR = repmat(eye(3,3), [1,1, arg.iter+1]);

if (strcmp(arg.Minimize, 'plane') && isempty(arg.Normals))
    arg.Normals = lsqnormest(q,4);
end

if strcmp(arg.Matching, 'Delaunay')
    DT = DelaunayTri(transpose(q));
end

if strcmp(arg.Matching, 'kDtree')
    kdOBJ = KDTreeSearcher(transpose(q));
end

if arg.EdgeRejection
    if isempty(arg.Boundary)
        bdr = find_bound(q, arg.Triangulation);
    else
        bdr = arg.Boundary;
    end
end
if arg.Extrapolation

    qq = [ones(1,arg.iter+1);zeros(6,arg.iter+1)];

    dq = zeros(7,arg.iter+1);
    theta = zeros(1,arg.iter+1);
end
t(1) = toc;

for k=1:arg.iter

    switch arg.Matching
        case 'bruteForce'
            [match mindist] = match_bruteForce(q,pt);
        case 'Delaunay'
            [match mindist] = match_Delaunay(q,pt,DT);
        case 'kDtree'
            [match mindist] = match_kDtree(q,pt,kdOBJ);
    end

    if arg.EdgeRejection
        p_idx = not(ismember(match, bdr));
        q_idx = match(p_idx);
        mindist = mindist(p_idx);
    else
        p_idx = true(1, Np);
        q_idx = match;
    end

    if arg.WorstRejection
        edge = round((1-arg.WorstRejection)*sum(p_idx));
        pairs = find(p_idx);
        [~, idx] = sort(mindist);
        p_idx(pairs(idx(edge:end))) = false;
        q_idx = match(p_idx);
        mindist = mindist(p_idx);
    end

    if k == 1
        ER(k) = sqrt(sum(mindist.^2)/length(mindist));
    end

    switch arg.Minimize
        case 'point'

            weights = arg.Weight(match);
            [R,T] = eq_point(q(:,q_idx),pt(:,p_idx), weights(p_idx));
        case 'plane'
            weights = arg.Weight(match);
            [R,T] = eq_plane(q(:,q_idx),pt(:,p_idx),arg.Normals(:,q_idx),weights(p_idx));
        case 'lmaPoint'
            [R,T] = eq_lmaPoint(q(:,q_idx),pt(:,p_idx));
    end

    TR(:,:,k+1) = R*TR(:,:,k);
    TT(:,:,k+1) = R*TT(:,:,k)+T;

    pt = TR(:,:,k+1) * p + repmat(TT(:,:,k+1), 1, Np);

    ER(k+1) = rms_error(q(:,q_idx), pt(:,p_idx));

    if arg.Extrapolation
        qq(:,k+1) = [rmat2quat(TR(:,:,k+1));TT(:,:,k+1)];
        dq(:,k+1) = qq(:,k+1) - qq(:,k);
        theta(k+1) = (180/pi)*acos(dot(dq(:,k),dq(:,k+1))/(norm(dq(:,k))*norm(dq(:,k+1))));
        if arg.Verbose
            disp(['Direction change ' num2str(theta(k+1)) ' degree in iteration ' num2str(k)]);
        end
        if k>2 && theta(k+1) < 10 && theta(k) < 10
            d = [ER(k+1), ER(k), ER(k-1)];
            v = [0, -norm(dq(:,k+1)), -norm(dq(:,k))-norm(dq(:,k+1))];
            vmax = 25 * norm(dq(:,k+1));
            dv = extrapolate(v,d,vmax);
            if dv ~= 0
                q_mark = qq(:,k+1) + dv * dq(:,k+1)/norm(dq(:,k+1));
                q_mark(1:4) = q_mark(1:4)/norm(q_mark(1:4));
                qq(:,k+1) = q_mark;
                TR(:,:,k+1) = quat2rmat(qq(1:4,k+1));
                TT(:,:,k+1) = qq(5:7,k+1);

                pt = TR(:,:,k+1) * p + repmat(TT(:,:,k+1), 1, Np);

                switch arg.Matching
                    case 'bruteForce'
                        [~, mindist] = match_bruteForce(q,pt);
                    case 'Delaunay'
                        [~, mindist] = match_Delaunay(q,pt,DT);
                    case 'kDtree'
                        [~, mindist] = match_kDtree(q,pt,kdOBJ);
                end
                ER(k+1) = sqrt(sum(mindist.^2)/length(mindist));
            end
        end
    end
    t(k+1) = toc;
end
if not(arg.ReturnAll)
    TR = TR(:,:,end);
    TT = TT(:,:,end);
end

function [match mindist] = match_bruteForce(q, p)
    m = size(p,2);
    n = size(q,2);
    match = zeros(1,m);
    mindist = zeros(1,m);
    for ki=1:m
        d=zeros(1,n);
        for ti=1:3
            d=d+(q(ti,:)-p(ti,ki)).^2;
        end
        [mindist(ki),match(ki)]=min(d);
    end

    mindist = sqrt(mindist);

function [match mindist] = match_Delaunay(q, p, DT)
	match = transpose(nearestNeighbor(DT, transpose(p)));
	mindist = sqrt(sum((p-q(:,match)).^2,1));

function [match mindist] = match_kDtree(~, p, kdOBJ)
	[match mindist] = knnsearch(kdOBJ,transpose(p));
    match = transpose(match);

function [R,T] = eq_point(q,p,weights)
m = size(p,2);
n = size(q,2);

weights = weights ./ sum(weights);

q_bar = q * transpose(weights);
q_mark = q - repmat(q_bar, 1, n);

q_mark = q_mark .* repmat(weights, 3, 1);

p_bar = p * transpose(weights);
p_mark = p - repmat(p_bar, 1, m);

N = p_mark*transpose(q_mark);
[U,~,V] = svd(N);
R = V*diag([1 1 det(U*V')])*transpose(U);
T = q_bar - R*p_bar;

function [R,T] = eq_plane(q,p,n,weights)
n = n .* repmat(weights,3,1);
c = cross(p,n);
cn = vertcat(c,n);
C = cn*transpose(cn);
b = - [sum(sum((p-q).*repmat(cn(1,:),3,1).*n));
       sum(sum((p-q).*repmat(cn(2,:),3,1).*n));
       sum(sum((p-q).*repmat(cn(3,:),3,1).*n));
       sum(sum((p-q).*repmat(cn(4,:),3,1).*n));
       sum(sum((p-q).*repmat(cn(5,:),3,1).*n));
       sum(sum((p-q).*repmat(cn(6,:),3,1).*n))];

X = C\b;
cx = cos(X(1)); cy = cos(X(2)); cz = cos(X(3));
sx = sin(X(1)); sy = sin(X(2)); sz = sin(X(3));
R = [cy*cz cz*sx*sy-cx*sz cx*cz*sy+sx*sz;
     cy*sz cx*cz+sx*sy*sz cx*sy*sz-cz*sx;
     -sy cy*sx cx*cy];

T = X(4:6);

function [R,T] = eq_lmaPoint(q,p)
Rx = @(a)[1     0       0;
          0     cos(a)  -sin(a);
          0     sin(a)  cos(a)];

Ry = @(b)[cos(b)    0   sin(b);
          0         1   0;
          -sin(b)   0   cos(b)];

Rz = @(g)[cos(g)    -sin(g) 0;
          sin(g)    cos(g)  0;
          0         0       1];
Rot = @(x)Rx(x(1))*Ry(x(2))*Rz(x(3));
myfun = @(x,xdata)Rot(x(1:3))*xdata+repmat(x(4:6),1,length(xdata));
options = optimset('Algorithm', 'levenberg-marquardt');
x = lsqcurvefit(myfun, zeros(6,1), p, q, [], [], options);
R = Rot(x(1:3));
T = x(4:6);

function [dv] = extrapolate(v,d,vmax)
p1 = polyfit(v,d,1);
p2 = polyfit(v,d,2);
v1 = -p1(2)/p1(1);
v2 = -p2(2)/(2*p2(1));
if issorted([0 v2 v1 vmax]) || issorted([0 v2 vmax v1])
    disp('Parabolic update!');
    dv = v2;
elseif issorted([0 v1 v2 vmax]) || issorted([0 v1 vmax v2])...
        || (v2 < 0 && issorted([0 v1 vmax]))
    disp('Line based update!');
    dv = v1;
elseif v1 > vmax && v2 > vmax
    disp('Maximum update!');
    dv = vmax;
else
    disp('No extrapolation!');
    dv = 0;
end

function ER = rms_error(p1,p2)
dsq = sum(power(p1 - p2, 2),1);
ER = sqrt(mean(dsq));

function quaternion = rmat2quat(R)
Qxx = R(1,1,:);
Qxy = R(1,2,:);
Qxz = R(1,3,:);
Qyx = R(2,1,:);
Qyy = R(2,2,:);
Qyz = R(2,3,:);
Qzx = R(3,1,:);
Qzy = R(3,2,:);
Qzz = R(3,3,:);
w = 0.5 * sqrt(1+Qxx+Qyy+Qzz);
x = 0.5 * sign(Qzy-Qyz) .* sqrt(1+Qxx-Qyy-Qzz);
y = 0.5 * sign(Qxz-Qzx) .* sqrt(1-Qxx+Qyy-Qzz);
z = 0.5 * sign(Qyx-Qxy) .* sqrt(1-Qxx-Qyy+Qzz);
quaternion = reshape([w;x;y;z],4,[]);

function R = quat2rmat(quaternion)
q0(1,1,:) = quaternion(1,:);
qx(1,1,:) = quaternion(2,:);
qy(1,1,:) = quaternion(3,:);
qz(1,1,:) = quaternion(4,:);
R = [q0.^2+qx.^2-qy.^2-qz.^2 2*qx.*qy-2*q0.*qz 2*qx.*qz+2*q0.*qy;
     2*qx.*qy+2*q0.*qz q0.^2-qx.^2+qy.^2-qz.^2 2*qy.*qz-2*q0.*qx;
     2*qx.*qz-2*q0.*qy 2*qy.*qz+2*q0.*qx q0.^2-qx.^2-qy.^2+qz.^2];

function n = lsqnormest(p, k)
m = size(p,2);
n = zeros(3,m);
v = ver('stats');
if str2double(v.Version) >= 7.5
    neighbors = transpose(knnsearch(transpose(p), transpose(p), 'k', k+1));
else
    neighbors = k_nearest_neighbors(p, p, k+1);
end
for i = 1:m
    x = p(:,neighbors(2:end, i));
    p_bar = 1/k * sum(x,2);

    P = (x - repmat(p_bar,1,k)) * transpose(x - repmat(p_bar,1,k));

    [V,D] = eig(P);

    [~, idx] = min(diag(D));

    n(:,i) = V(:,idx);
end

function [neighborIds neighborDistances] = k_nearest_neighbors(dataMatrix, queryMatrix, k)
numDataPoints = size(dataMatrix,2);
numQueryPoints = size(queryMatrix,2);
neighborIds = zeros(k,numQueryPoints);
neighborDistances = zeros(k,numQueryPoints);
D = size(dataMatrix, 1);
for i=1:numQueryPoints
    d=zeros(1,numDataPoints);
    for t=1:D
        d=d+(dataMatrix(t,:)-queryMatrix(t,i)).^2;
    end
    for j=1:k
        [s,t] = min(d);
        neighborIds(j,i)=t;
        neighborDistances(j,i)=sqrt(s);
        d(t) = NaN;
    end
end

function bound = find_bound(pts, poly)

poly = double(poly);
pts = double(pts);

TR = TriRep(poly, pts(1,:)', pts(2,:)', pts(3,:)');
FF = freeBoundary(TR);

bound = FF(:,1);
