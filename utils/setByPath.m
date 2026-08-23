function S = setByPath(S, path, val)
%SETBYPATH Write nested struct field, e.g. 'IMU.gyroBiasDps(2)' = val.
parts = strsplit(path, '.');
S = assign(S, parts, val);
end
function s = assign(s, parts, val)
tok = parts{1};
idx = [];
k = strfind(tok, '(');
if ~isempty(k)
    idx = str2double(tok(k(1)+1:end-1));
    tok = tok(1:k(1)-1);
end
if numel(parts) == 1
    if isempty(idx)
        s.(tok) = val;
    else
        tmp = s.(tok);
        tmp(idx) = val;
        s.(tok) = tmp;
    end
else
    if isempty(idx)
        s.(tok) = assign(s.(tok), parts(2:end), val);
    else
        tmp = s.(tok);
        tmp(idx) = assign(tmp(idx), parts(2:end), val);
        s.(tok) = tmp;
    end
end
end
