function g = localGravity(cfg, h, latDeg)
%LOCALGRAVITY Gravity magnitude [m/s^2].
% h is altitude relative to INS.refH.  WGS84 mode adds latitude dependence
% while preserving cfg.INS.gravity exactly at the configured reference.
g0 = cfg.INS.gravity;
if nargin < 2 || isempty(h), h = 0; end
if nargin < 3 || isempty(latDeg), latDeg = cfg.INS.refLat; end
if isfield(cfg.INS,'earthModel') && strcmp(cfg.INS.earthModel,'wgs84')
    e2 = 6.6943799901413165e-3; k = 1.93185265241e-3;
    normal = @(lat) 9.7803253359*(1+k*sin(lat).^2)./sqrt(1-e2*sin(lat).^2);
    g = g0 + normal(deg2rad(latDeg)) - normal(deg2rad(cfg.INS.refLat)) - 3.086e-6*h;
else
    g = g0 - 3.086e-6*h;
end
end
