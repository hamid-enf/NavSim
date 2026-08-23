function r = lla2ecef(lla)
%LLA2ECEF WGS84 geodetic [lat deg; lon deg; h m] to ECEF [m].
a = 6378137.0;
e2 = 6.6943799901413165e-3;
lat = deg2rad(lla(1)); lon = deg2rad(lla(2)); h = lla(3);
s = sin(lat); c = cos(lat); N = a / sqrt(1-e2*s*s);
r = [(N+h)*c*cos(lon); (N+h)*c*sin(lon); (N*(1-e2)+h)*s];
end
