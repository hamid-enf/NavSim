function eul = quat2eul(q)
%QUAT2EUL Euler [roll;pitch;yaw] from scalar-first quaternion.
eul = dcm2eul(quat2dcm(q));
end
