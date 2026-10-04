function binname=mcpath(fname, ext)

p=getvarfrom({'caller','base'},'ISO2MESH_BIN');
binname=[];
if(isempty(p))

	tempname=[fileparts(which(mfilename)) filesep 'bin' filesep fname];
	if(exist([fileparts(which(mfilename)) filesep 'bin'])==7)
        if(nargin>=2)
            if(exist([tempname ext],'file'))
                binname=[tempname ext];
            else
                binname=fname;
            end
        else
		    binname=tempname;
        end
	else
		binname=fname;
	end
else
	binname=[p filesep fname];
end
