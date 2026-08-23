function lla = ned2lla(ned, lla0)
%NED2LLA Reference-tangent NED chord coordinates to WGS84 geodetic LLA.
r0 = lla2ecef(lla0);
r = r0 + nedRotation(lla0)' * ned(:);
lla = ecef2lla(r);
end
