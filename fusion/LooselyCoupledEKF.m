classdef LooselyCoupledEKF < handle
%LOOSELYCOUPLEDEKF 15-state error-state EKF for GNSS/INS (loosely coupled).
%
% Error state dx = [dp(3); dv(3); dphi(3); dbg(3); dba(3)]
%   dp   : position error          (NED, m)
%   dv   : velocity error          (NED, m/s)
%   dphi : attitude error, small-angle of estimated nav frame
%   dbg  : residual gyro bias      (rad/s)
%   dba  : residual accel bias     (m/s^2)
%
% Local-frame error model (no Earth/transport rates), errors = true - est:
%   dp_dot   = dv
%   dv_dot   = [fn x] dphi - C dba + noise
%   dphi_dot = +C dbg + noise        (sign follows the true-minus-est convention)
%   bias     : random walk
% Corrections are fed back (closed loop): dx is consumed and zeroed.

properties
    x = zeros(15,1)
    P = zeros(15)
    cfg
    initialized = false
    lastInnov = zeros(3,1)
    lastNIS = 0
end

methods
    function updateParams(obj, cfg) %#ok<INUSD>
        % (EKF parameters are read live from cfg in initState/predict)
    end

    function initState(obj, cfg)
        s = cfg.Fusion;
        sig = [ ones(3,1)*s.p0pos;
                ones(3,1)*s.p0vel;
                ones(3,1)*deg2rad(s.p0attDeg);
                ones(3,1)*deg2rad(s.p0gyroBiasDps);
                ones(3,1)*s.p0accelBias ];
        obj.P = diag(sig.^2);
        obj.x = zeros(15,1);
        obj.initialized = true;
        obj.cfg = cfg;
    end

    function predict(obj, C, fb, dt, cfg)
        if ~obj.initialized, obj.initState(cfg); end
        obj.cfg = cfg;
        s  = cfg.Fusion;
        fn = C * fb;
        F  = eye(15);
        F(1:3, 4:6)   = eye(3) * dt;
        F(4:6, 7:9)   = skew(fn) * dt;
        F(4:6, 13:15) = -C * dt;
        F(7:9, 10:12) = C * dt;   % error = true - est convention: dphi_dot = +C*dbg
        qa  = (s.qa * s.qScale)^2;                    % (m/s^2)^2/Hz
        qg  = (deg2rad(s.qg) * s.qScale)^2;           % (rad/s)^2/Hz
        qbg = (deg2rad(s.qbg) * s.qScale)^2;
        qba = (s.qba * s.qScale)^2;
        Qd = zeros(15);
        Qd(1:3,1:3)     = eye(3) * qa * dt^3 / 3;
        Qd(1:3,4:6)     = eye(3) * qa * dt^2 / 2;
        Qd(4:6,1:3)     = Qd(1:3,4:6)';
        Qd(4:6,4:6)     = eye(3) * qa * dt;
        Qd(7:9,7:9)     = eye(3) * qg * dt;
        Qd(10:12,10:12) = eye(3) * qbg * dt;
        Qd(13:15,13:15) = eye(3) * qba * dt;
        obj.P = F * obj.P * F' + Qd;
        obj.P = 0.5 * (obj.P + obj.P');
    end

    function updatePos(obj, zp, R)
        H = [eye(3), zeros(3,12)];
        obj.kalman(zp, H, R * obj.cfg.Fusion.rScale);
    end

    function updateVel(obj, zv, Rv)
        H = [zeros(3,3), eye(3), zeros(3,9)];
        obj.kalman(zv, H, Rv * obj.cfg.Fusion.rScale);
    end

    function kalman(obj, z, H, R)
        innov = z - H * obj.x;
        S = H * obj.P * H' + R;
        K = (obj.P * H') / S;
        obj.x = obj.x + K * innov;
        IKH = eye(15) - K * H;
        obj.P = IKH * obj.P * IKH' + K * R * K';   % Joseph form
        obj.P = 0.5 * (obj.P + obj.P');
        obj.lastInnov = innov;
        obj.lastNIS = innov' * (S \ innov);
    end

    function dx = consumeDx(obj)
        dx = obj.x;
        obj.x(:) = 0;
    end

    function s = sigmas(obj)
        s = sqrt(max(diag(obj.P), 0));
    end
end
end
