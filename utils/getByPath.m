function v = getByPath(S, path)
%GETBYPATH Read nested struct field, e.g. 'IMU.gyroBiasDps(2)'.
v = walk(S, strsplit(path, '.'));
end
function v = walk(s, parts)
for i = 1:numel(parts)
    tok = parts{i};
    idx = [];
    k = strfind(tok, '(');
    if ~isempty(k)
        idx = str2double(tok(k(1)+1:end-1));
        tok = tok(1:k(1)-1);
    end
    s = s.(tok);
    if ~isempty(idx)
        s = s(idx);
    end
end
v = s;
end
