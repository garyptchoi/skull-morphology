function exesuff=fallbackexeext(exesuffix, exename)

exesuff=exesuffix;
if(strcmp(exesuff,'.mexa64') & exist([mcpath(exename) exesuff],'file')==0)
        exesuff='.mexglx';
end
if(strcmp(exesuff,'.mexmaci64') & exist([mcpath(exename) exesuff],'file')==0)
        exesuff='.mexmaci';
end
if(strcmp(exesuff,'.mexmaci') & exist([mcpath(exename) exesuff],'file')==0)
        exesuff='.mexmac';
end
if(exist([mcpath(exename) exesuff],'file')==0)
        exesuff='';
end

if(exist([mcpath(exename) exesuff],'file')==0)
        if(strcmp(exename,'tetgen'))
               return;
        end
        error([ 'The following executable:\n' ...
                        '\t%s%s\n' ...
                        'is missing. Please download it from ' ...
                        'https://github.com/fangq/iso2mesh/tree/master/bin/ ' ...
                        'and save it to the above path, then rerun the script.\n' ...
                ],mcpath(exename),getexeext);
end
