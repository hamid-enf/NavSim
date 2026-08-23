function ned = lla2ned(lla, lla0)
%LLA2NED Geodetic [lat(deg);lon(deg);h(m)] -> local NED (m), WGS84 radii.
a  = 6378137.0;
e2 = 6.69437999014e-3;
lat  = deg2rad(lla(1));  lon  = deg2rad(lla(2));
lat0 = deg2rad(lla0(1)); lon0 = deg2rad(lla0(2));
s0 = sin(lat0);
M = a*(1-e2) / (1 - e2*s0*s0)^1.5;   % meridian radius of curvature
N = a / sqrt(1 - e2*s0*s0);          % transverse radius of curvature
h0 = lla0(3);
ned = [ (lat - lat0) * (M + h0);
        (lon - lon0) * cos(lat0) * (N + h0);
        -(lla(3) - h0) ];
end
