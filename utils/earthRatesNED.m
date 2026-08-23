function [wie, wen, win] = earthRatesNED(lla, v, cfg)
%EARTHRATESNED Earth, transport and inertial navigation-frame rates [rad/s].
lat = deg2rad(lla(1)); h = lla(3); v = v(:);
[RM,RN] = earthRadii(lat);
if isfield(cfg.INS,'useEarthRate') && cfg.INS.useEarthRate
    omega = 7.292115e-5;
    wie = omega * [cos(lat); 0; -sin(lat)];
else
    wie = zeros(3,1);
end
if isfield(cfg.INS,'useTransportRate') && cfg.INS.useTransportRate
    c = cos(lat);
    if abs(c) < 1e-8, c = sign(c + eps)*1e-8; end
    wen = [v(2)/(RN+h); -v(1)/(RM+h); -v(2)*tan(lat)/(RN+h)];
else
    wen = zeros(3,1);
end
win = wie + wen;
end
