function C = eul2dcm(eul)
%EUL2DCM Body->nav DCM from Euler angles [roll;pitch;yaw] (ZYX, aerospace).
r = eul(1); p = eul(2); y = eul(3);
cr=cos(r); sr=sin(r); cp=cos(p); sp=sin(p); cy=cos(y); sy=sin(y);
C = [ cp*cy,  sr*sp*cy - cr*sy,  cr*sp*cy + sr*sy;
      cp*sy,  sr*sp*sy + cr*cy,  cr*sp*sy - sr*cy;
      -sp,    sr*cp,             cr*cp            ];
end
