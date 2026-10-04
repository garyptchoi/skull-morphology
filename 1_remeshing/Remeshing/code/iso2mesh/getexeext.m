function exesuff=getexeext()

exesuff='.exe';
if(isunix)
	exesuff=['.',mexext];
end
if(isoctavemesh)
   if(~ispc)
      if(~ismac)
	   if(isempty(regexp(computer,'86_64')))
	      exesuff='.mexglx';
	   else
              exesuff='.mexa64';
	   end
      else
           if(isempty(regexp(computer,'86_64')))
              exesuff='.mexmaci';
           else
              exesuff='.mexmaci64';
           end
      end
   else
      exesuff='.exe';
   end
end
