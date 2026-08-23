function Cen = nedRotation(lla)
%NEDROTATION ECEF-to-NED DCM at geodetic LLA [deg, deg, m].
lat = deg2rad(lla(1)); lon = deg2rad(lla(2));
sl = sin(lat); cl = cos(lat); so = sin(lon); co = cos(lon);
Cen = [-sl*co, -sl*so,  cl; ...
          -so,     co,   0; ...
       -cl*co, -cl*so, -sl];
end
