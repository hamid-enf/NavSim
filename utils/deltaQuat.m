function dq = deltaQuat(a)
%DELTAQUAT Rotation vector (rad) to incremental quaternion (scalar-first).
n = norm(a);
if n < 1e-12
    dq = [1; a(:)/2];
else
    dq = [cos(n/2); a(:)/n * sin(n/2)];
end
end
