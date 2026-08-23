function truth = earthTruth(raw, cfg, refLla)
%EARTHTRUTH Map a reference-tangent trajectory into a WGS84 local-level state.
% raw p/v/a and attitude are expressed in the fixed NED frame at refLla.
r0 = lla2ecef(refLla);
Cen0 = nedRotation(refLla);
r = r0 + Cen0' * raw.p(:);
lla = ecef2lla(r);
Cen = nedRotation(lla);
T = Cen * Cen0';                 % reference NED -> current local NED
v = T * raw.v(:);
[wie,wen,win] = earthRatesNED(lla, v, cfg);
a = T * raw.a(:) - cross(wen, v);
Cbn = T * eul2dcm(raw.eul);
eul = dcm2eul(Cbn);
% The reference NED frame is Earth-fixed.  Add Earth rotation to the
% body/Earth rate to obtain the inertial gyro input.
wEbB = eulRates2body(raw.eul, raw.eulDot);
wIbB = wEbB + Cbn' * wie;
wNbB = wIbB - Cbn' * win;
eulDot = bodyRates2eul(eul, wNbB);
g = localGravity(cfg, lla(3)-refLla(3), lla(1));
gn = [0;0;g];
if isfield(cfg.INS,'useCoriolis') && cfg.INS.useCoriolis
    coriolis = cross(2*wie + wen, v);
else
    coriolis = zeros(3,1);
end
fB = Cbn' * (a - gn + coriolis);
truth = struct('t',raw.t,'p',raw.p(:),'v',v,'a',a,'eul',eul, ...
    'eulDot',eulDot,'lla',lla,'C',Cbn,'wIb',wIbB,'fB',fB, ...
    'wie',wie,'wen',wen);
end
