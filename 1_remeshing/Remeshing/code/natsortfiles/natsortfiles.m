function [X,ndx] = natsortfiles(X,varargin)

assert(iscell(X),'First input <X> must be a cell array.')
tmp = cellfun('isclass',X,'char') & cellfun('size',X,1)<2 & cellfun('ndims',X)<3;
assert(all(tmp(:)),'First input <X> must be a cell array of strings (1xN character).')

[pth,nam,ext] = cellfun(@fileparts,X(:),'UniformOutput',false);

pth = regexp(pth,'[/\\]','split');
len = cellfun('length',pth);
vec(1:numel(len)) = {''};

[~,ndx] = natsort(ext,varargin{:});
[~,ind] = natsort(nam(ndx),varargin{:});
ndx = ndx(ind);
for k = max(len):-1:1
	idx = len>=k;
	vec(~idx) = {''};
	vec(idx) = cellfun(@(c)c(k),pth(idx));
	[~,ind] = natsort(vec(ndx),varargin{:});
	ndx = ndx(ind);
end

ndx = reshape(ndx,size(X));
X = X(ndx);

end
