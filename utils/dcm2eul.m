function eul = dcm2eul(C)
%DCM2EUL Euler angles [roll;pitch;yaw] from body->nav DCM (ZYX order).
eul = [ atan2(C(3,2), C(3,3));
       -asin(max(-1, min(1, C(3,1))));
        atan2(C(2,1), C(1,1)) ];
end
