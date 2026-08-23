classdef INSMechanization < handle
%INSMECHANIZATION Strapdown INS mechanization in a local NED frame.
%
%   gyro  -> attitude (quaternion integration)
%   accel --(C_b2n)--> nav frame -> (+ gravity) -> velocity -> position
%
% First-order coning/sculling terms and Earth/transport rates are ignored
% (educational local-frame model, documented). Supports variable dt and
% error-state feedback corrections from the fusion filter.

properties
    p = zeros(3,1)      % position NED [m]
    v = zeros(3,1)      % velocity NED [m/s]
    q = [1;0;0;0]       % attitude quaternion body->nav
    C = eye(3)          % cached DCM body->nav
    grav = 9.80665
    fnLast = zeros(3,1) % specific force used in nav frame
end

methods
    function reset(obj, p0, v0, eul0, cfg)
        obj.p = p0(:);
        obj.v = v0(:);
        obj.q = eul2quat(eul0);
        obj.C = quat2dcm(obj.q);
        if nargin >= 5
            obj.grav = cfg.INS.gravity;
        end
    end

    function step(obj, w, f, dt, grav)
        if nargin >= 5
            obj.grav = grav;
        end
        % attitude update (single-sample, no coning correction)
        qNew = quatMul(obj.q, deltaQuat(w * dt));
        qNew = qNew ./ norm(qNew);
        Cnew = quat2dcm(qNew);
        % mid-frame rotation for the specific force (cheap trapezoid)
        Cm = 0.5 * (obj.C + Cnew);
        fn = Cm * f;
        vv = obj.v + (fn + [0; 0; obj.grav]) * dt;
        obj.p = obj.p + 0.5 * (obj.v + vv) * dt;  % trapezoidal position
        obj.v = vv;
        obj.q = qNew;
        obj.C = Cnew;
        obj.fnLast = fn;
    end

    function correctState(obj, dp, dv, dphi)
        % Apply error-state feedback: state <- state + error estimate.
        obj.p = obj.p + dp(:);
        obj.v = obj.v + dv(:);
        obj.C = (eye(3) - skew(dphi(:))) * obj.C;
        obj.q = dcm2quat(obj.C);
    end

    function eul = eul(obj)
        eul = dcm2eul(obj.C);
    end
end
end
