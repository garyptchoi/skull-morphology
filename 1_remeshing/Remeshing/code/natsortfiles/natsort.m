function [X,ndx,dbg] = natsort(X,xpr,varargin)

assert(iscell(X),'First input <X> must be a cell array.')
tmp = cellfun('isclass',X,'char') & 2>cellfun('size',X,1) & 3>cellfun('ndims',X);
assert(all(tmp(:)),'First input <X> must be a cell array of strings (1xN character).')

if nargin<2 || isnumeric(xpr)&&isempty(xpr)
	xpr = '\d+';
else
	assert(ischar(xpr)&&isrow(xpr),'Second input <xpr> must be a regular expression.')
end

tmp = cellfun('isclass',varargin,'char') & 1==cellfun('size',varargin,1) & 2==cellfun('ndims',varargin);
assert(all(tmp(:)),'All optional arguments must be strings (1xN character).')

MatL = strcmpi(varargin,'matchcase');
CasL = strcmpi(varargin,'ignorecase')|MatL;

DesL = strcmpi(varargin,'descend');
DirL = strcmpi(varargin,'ascend')|DesL;

BefL = strcmpi(varargin,'beforechar');
AftL = strcmpi(varargin,'afterchar');
RsoL = strcmpi(varargin,'asdigit')|BefL|AftL;

FmtL = ~(CasL|DirL|RsoL);

if nnz(DirL)>1
	error('Sort direction is overspecified:%s\b.',sprintf(' ''%s'',',varargin{DirL}))
end

if nnz(RsoL)>1
	error('Relative sort-order is overspecified:%s\b.',sprintf(' ''%s'',',varargin{RsoL}))
end

FmtN = nnz(FmtL);
if FmtN>1
	error('Overspecified optional arguments:%s\b.',sprintf(' ''%s'',',varargin{FmtL}))
end

[MtS,MtE,MtC,SpC] = regexpi(X(:),xpr,'start','end','match','split',varargin{CasL});

MtcD = cellfun(@minus,MtE,MtS,'UniformOutput',false);
LenZ = cellfun('length',X(:))-cellfun(@sum,MtcD);
LenY = max(LenZ);
LenX = numel(MtC);

dbg = cell(LenX,LenY);
NuI = false(LenX,LenY);
ChI = false(LenX,LenY);
ChA = char(double(ChI));

ndx = 1:LenX;
for k = ndx(LenZ>0)

	ChI(k,1:LenZ(k)) = true;
	if ~isempty(MtS{k})
		tmp = MtE{k} - cumsum(MtcD{k});
		dbg(k,tmp) = MtC{k};
		NuI(k,tmp) = true;
		ChI(k,tmp) = false;
	end

	if any(ChI(k,:))
		tmp = SpC{k};
		ChA(k,ChI(k,:)) = [tmp{:}];
	end
end

if FmtN
	fmt = varargin{FmtL};
	err = ['Format specifier results in an empty output from sscanf: ''',fmt,''''];
	P = '(?<!%)(%%)*%';
	[T,S] = regexp(fmt,[P,'(\d*)(b|d|i|u|o|x|f|e|g|l(d|i|u|o|x))'],'tokens','split');
	assert(isscalar(T),'Unsupported optional argument: ''%s''',fmt)
	assert(isempty(T{1}{2}),'Format specifier cannot include field-width: ''%s''',fmt)
	switch T{1}{3}(1)
		case 'b'
			fmt = regexprep(fmt,[P,'(\*?)b'],'$1%$2[01]');
			val = dbg(NuI);
			if numel(S{1})<2 || ~strcmpi('0B',S{1}(end-1:end))

				val = regexprep(val,'(0B)?([01]+)','$2','ignorecase');
			end
			val = cellfun(@(s)sscanf(s,fmt),val, 'UniformOutput',false);
			assert(~any(cellfun('isempty',val)),err)
			NuA(NuI) = cellfun(@(s)sum(pow2(s-48,numel(s)-1:-1:0)),val);
		case 'l'
			NuA(NuI) = cellfun(@(s)sscanf(s,fmt),dbg(NuI));
		otherwise
			NuA(NuI) = sscanf(sprintf('%s\v',dbg{NuI}),[fmt,'\v']);
	end
else
	NuA(NuI) = sscanf(sprintf('%s\v',dbg{NuI}),'%f\v');
end

NuA(~NuI) = 0;
NuA = reshape(NuA,LenX,LenY);

if nargout>2
	for k = reshape(find(NuI),1,[])
		dbg{k} = NuA(k);
	end
	for k = reshape(find(ChI),1,[])
		dbg{k} = ChA(k);
	end
end

if ~any(MatL)
	ChA = upper(ChA);
end

ide = ndx.';

for n = LenY:-1:1

	[C,idc] = sort(ChA(ndx,n),1,varargin{DirL});
	[~,idn] = sort(NuA(ndx,n),1,varargin{DirL});

	jdc = ChI(ndx(idc),n);
	jdn = NuI(ndx(idn),n);
	jde = ~ChI(ndx,n)&~NuI(ndx,n);

	jdo = any(AftL)|(~any(BefL)&C<48);

	if any(DesL)
		idx = [idc(jdc&~jdo);idn(jdn);idc(jdc&jdo);ide(jde)];
	else
		idx = [ide(jde);idc(jdc&jdo);idn(jdn);idc(jdc&~jdo)];
	end
	ndx = ndx(idx);
end

ndx  = reshape(ndx,size(X));
X = X(ndx);

end
