function [RM, RN] = earthRadii(lat)
%EARTHRADII WGS84 meridian and prime-vertical radii [m].
% lat is geodetic latitude in radians.
a = 6378137.0;
e2 = 6.6943799901413165e-3;
s = sin(lat);
den = sqrt(1 - e2*s*s);
RN = a / den;
RM = a*(1-e2) / den^3;
end
