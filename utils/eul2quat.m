function q = eul2quat(eul)
%EUL2QUAT Scalar-first quaternion from Euler [roll;pitch;yaw] (ZYX).
q = dcm2quat(eul2dcm(eul));
end
