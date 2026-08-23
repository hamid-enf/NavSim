function lla = ecef2lla(r)
%ECEF2LLA ECEF [m] to WGS84 geodetic [lat deg; lon deg; h m].
a = 6378137.0;
e2 = 6.6943799901413165e-3;
x = r(1); y = r(2); z = r(3);
lon = atan2(y,x); p = hypot(x,y);
if p < 1e-9
    lat = sign(z)*pi/2;
    h = abs(z) - a*sqrt(1-e2);
else
    lat = atan2(z, p*(1-e2));
    for k = 1:10
        s = sin(lat); N = a/sqrt(1-e2*s*s);
        h = p/cos(lat) - N;
        latNew = atan2(z, p*(1-e2*N/(N+h)));
        if abs(latNew-lat) < 1e-14, lat = latNew; break; end
        lat = latNew;
    end
    s = sin(lat); N = a/sqrt(1-e2*s*s);
    h = p/cos(lat) - N;
end
lla = [rad2deg(lat); rad2deg(lon); h];
end
