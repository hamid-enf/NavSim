function ned = lla2ned(lla, lla0)
%LLA2NED Geodetic LLA to exact ECEF chord coordinates in reference NED.
r0 = lla2ecef(lla0);
r = lla2ecef(lla);
ned = nedRotation(lla0) * (r-r0);
end
