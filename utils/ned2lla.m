function lla = ned2lla(ned, lla0)
%NED2LLA Local NED (m) -> geodetic [lat(deg);lon(deg);h(m)], WGS84 radii.
a  = 6378137.0;
e2 = 6.69437999014e-3;
lat0 = deg2rad(lla0(1));
s0 = sin(lat0);
M = a*(1-e2) / (1 - e2*s0*s0)^1.5;
N = a / sqrt(1 - e2*s0*s0);
h0 = lla0(3);
lat = lat0 + ned(1) / (M + h0);
lon = deg2rad(lla0(2)) + ned(2) / ((N + h0)*cos(lat0));
lla = [rad2deg(lat); rad2deg(lon); h0 - ned(3)];
end
