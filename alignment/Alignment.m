classdef Alignment < handle
%ALIGNMENT Initial alignment simulation, two physically-honest modes:
%
%  STATIC (low speed, acceleration, and angular rate): coarse levelling:
%        phi   = atan2(-f_y, -f_z)
%        theta = atan2( f_x, sqrt(f_y^2+f_z^2))
%    plus magnetometer heading (true yaw + noise). Estimate converges as
%    1/sqrt(n) while averaging  -> the "alignment convergence" demo.
%
%  MOVING (|v0| > 1 m/s): "transfer alignment" coarse guess, i.e. another
%    nav source hands over attitude with a coarse random error (constant).
%    Convergence then happens later through the fusion filter during motion.
%
%  An extra user-set initial error can be added in both modes.

properties
    cfg
    t0 = 0
    n = 0
    sumF = zeros(3,1)
    estEul = zeros(3,1)
    yawMagErr = 0
    coarseErr = zeros(3,1)
    truthEul0 = zeros(3,1)
    isStatic = true
    active = false
end

methods
    function reset(obj, cfg, truth0)
        obj.cfg = cfg;
        obj.t0 = 0;
        obj.n = 0;
        obj.sumF = zeros(3,1);
        obj.truthEul0 = truth0.eul;
        obj.yawMagErr = deg2rad(cfg.Align.magHeadingSigmaDeg) * randn;
        obj.coarseErr = deg2rad(cfg.Align.coarseMovingSigmaDeg) * randn(3,1);
        % Low initial speed alone is insufficient (e.g. an accelerating
        % trajectory can start from rest).  Levelling is valid only when
        % both translational speed and acceleration are negligible.
        obj.isStatic  = norm(truth0.v) <= 1.0 && norm(truth0.a) <= 0.1 && ...
                        norm(truth0.eulDot) <= deg2rad(0.1);
        obj.estEul    = truth0.eul + [0.5; 0.5; 1.0];   % intentionally rough start
        obj.active    = cfg.Align.enabled && cfg.Align.duration > 0;
    end

    function update(obj, fm, truth)
        if ~obj.active, return; end
        obj.n = obj.n + 1;
        if obj.isStatic
            obj.sumF = obj.sumF + fm;
            mf = obj.sumF / obj.n;
            if obj.cfg.Align.coarseLevel
                phi   = atan2(-mf(2), -mf(3));
                theta = atan2(mf(1), hypot(mf(2), mf(3)));
                obj.estEul = [phi; theta; obj.truthEul0(3) + obj.yawMagErr];
            else
                obj.estEul = obj.truthEul0 + [0; 0; obj.yawMagErr];
            end
        else
            % transfer alignment: constant coarse error w.r.t. CURRENT truth
            obj.estEul = truth.eul + obj.coarseErr;
        end
    end

    function eul0 = finalize(obj)
        if obj.active
            eul0 = obj.estEul;
        else
            eul0 = obj.truthEul0;
        end
        if obj.cfg.Align.applyUserErr
            eul0 = eul0 + deg2rad(obj.cfg.Align.userErrDeg(:));
        end
    end
end
end
