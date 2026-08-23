function q = dcm2quat(C)
%DCM2QUAT Quaternion (scalar-first) from DCM (Shepperd's method).
tr = C(1,1) + C(2,2) + C(3,3);
if tr > 0
    s = sqrt(tr + 1.0) * 2;
    q = [0.25*s; (C(3,2)-C(2,3))/s; (C(1,3)-C(3,1))/s; (C(2,1)-C(1,2))/s];
elseif (C(1,1) > C(2,2)) && (C(1,1) > C(3,3))
    s = sqrt(1.0 + C(1,1) - C(2,2) - C(3,3)) * 2;
    q = [(C(3,2)-C(2,3))/s; 0.25*s; (C(1,2)+C(2,1))/s; (C(1,3)+C(3,1))/s];
elseif C(2,2) > C(3,3)
    s = sqrt(1.0 + C(2,2) - C(1,1) - C(3,3)) * 2;
    q = [(C(1,3)-C(3,1))/s; (C(1,2)+C(2,1))/s; 0.25*s; (C(2,3)+C(3,2))/s];
else
    s = sqrt(1.0 + C(3,3) - C(1,1) - C(2,2)) * 2;
    q = [(C(2,1)-C(1,2))/s; (C(1,3)+C(3,1))/s; (C(2,3)+C(3,2))/s; 0.25*s];
end
if q(1) < 0, q = -q; end
q = q ./ norm(q);
end
