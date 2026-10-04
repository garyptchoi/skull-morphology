function [isoctave verinfo]=isoctavemesh

verinfo='';
isoctave=(exist('OCTAVE_VERSION','builtin')~=0);
if(nargout==2 && isoctave)
    verinfo=OCTAVE_VERSION;
end
