function tempname=mwpath(fname)

p=getvarfrom({'caller','base'},'ISO2MESH_TEMP');
session=getvarfrom({'caller','base'},'ISO2MESH_SESSION');

username=getenv('USER');

if(isempty(username))
   username=getenv('UserName');
end

if(~isempty(username))
   username=['iso2mesh-' username];
end

tempname=[];
if(isempty(p))
      if(isoctavemesh & tempdir=='\')
		tempname=['.'  filesep session fname];
	else
		tdir=tempdir;
		if(tdir(end)~=filesep)
			tdir=[tdir filesep];
		end
		if(~isempty(username))
                    tdir=[tdir username filesep];
                    if(exist(tdir)==0) mkdir(tdir); end
        end
        if(nargin==0)
            tempname=tdir;
        else
            tempname=[tdir session fname];
        end
	end
else
	tempname=[p filesep session fname];
end
