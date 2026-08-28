classdef Alignment
%ALIGNMENT Initial alignment simulation.
%
% Roll/pitch: coarse levelling from the accelerometer while static
% (averaged, converges ~1/sqrt(n)); transfer-alignment coarse guess when
% the platform starts moving.
%
% Yaw (heading) is provided by a configurable model:
%   'magnetometer'  REAL magnetometer: the sensor measures the geomagnetic
%       field in the body frame (true field rotated by truth attitude,
%       plus hard-iron bias and Gaussian noise). The heading estimate is
%       the circular mean of per-sample heading solutions obtained by
%       levelling the measurement with the current roll/pitch estimate.
%       Effective accuracy ~ magNoiseT / (magFieldT*cos(inclination)) rad.
%   'gyrocompass'   Earth-rate alignment model: the heading error decays
%       exponentially toward zero with time constant gyrocompassTau.
%       NOTE: true stationary gyrocompassing converges at the earth rate
%       (hours); the default tau = 15 s is an *accelerated effective
%       constant* so the demo fits an alignment window. Set
%       gyrocompassTau ~ 4.4e4 s for the real physics.
%   'magStub'       LEGACY: heading = true yaw + Gaussian noise
%       (magHeadingSigmaDeg). Kept for backward compatibility.
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
        headingModel = 'magnetometer'
        Bn = [0; 0; 0]        % true geomagnetic field in nav (NED) frame [T]
        magBias = [0; 0; 0]   % hard-iron bias in body frame [T]
        magNoiseT = 0
        magSum = 1 + 0i       % circular-mean accumulator for magnetometer yaw
        nMag = 0
        yawEst = 0            % current yaw estimate [rad]
        gyrocompassTau = 15
end

methods
    function obj = Alignment()
            % Constructor (engine constructs then resets).
        end

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
            % ---------------- heading model setup ----------------
            if isfield(cfg.Align, 'headingModel')
                obj.headingModel = cfg.Align.headingModel;
            else
                obj.headingModel = 'magStub';   % legacy configs
            end
            F  = cfg.Align.magFieldT;
            inc = deg2rad(cfg.Align.magInclinationDeg);
            dec = deg2rad(cfg.Align.magDeclinationDeg);
            Fh = F * cos(inc);
            % NED: horizontal field points toward magnetic north (dec east
            % of true north); vertical (down) component is positive.
            obj.Bn = [Fh * cos(dec); Fh * sin(dec); F * sin(inc)];
            obj.magBias = [cfg.Align.magBiasT; 0; 0];
            obj.magNoiseT = cfg.Align.magNoiseT;
            obj.magSum = 1 + 0i;
            obj.nMag = 0;
            obj.yawEst = truth0.eul(3) + deg2rad(15);   % gyrocompass start offset
            obj.gyrocompassTau = max(cfg.Align.gyrocompassTau, 1e-3);
        end

        function update(obj, fm, truth, dt)
            if ~obj.active, return; end
            obj.n = obj.n + 1;
            if obj.isStatic
                obj.sumF = obj.sumF + fm;
                mf = obj.sumF / obj.n;
                if obj.cfg.Align.coarseLevel
                    phi   = atan2(-mf(2), -mf(3));
                    theta = atan2(mf(1), hypot(mf(2), mf(3)));
                else
                    phi = obj.estEul(1); theta = obj.estEul(2);
                end
                switch obj.headingModel
                    case 'magnetometer'
                        obj.yawEst = obj.magHeading(fm, truth, phi, theta);
                    case 'gyrocompass'
                        % Effective earth-rate alignment: exponential decay
                        % of the heading error (accelerated for education;
                        % see class doc for the real time constant).
                        obj.yawEst = obj.yawEst + ...
                            wrapPi(truth.eul(3) - obj.yawEst) * (1 - exp(-dt / obj.gyrocompassTau));
                    otherwise   % 'magStub' (legacy)
                        obj.yawEst = obj.truthEul0(3) + obj.yawMagErr;
                end
                obj.estEul = [phi; theta; obj.yawEst];
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

        function yawEst = magHeading(obj, ~, truth, phi, theta)
            % Real magnetometer model.
            % 1) True field in body frame from truth attitude + sensor errors.
            Cn2b = eul2dcm(truth.eul);
            Bb = Cn2b * obj.Bn + obj.magBias + obj.magNoiseT * randn(3,1);
            % 2) Level the measurement with the current roll/pitch estimate
            %    (rotate out pitch then roll about the vehicle axes).
            Rx = [1 0 0; 0 cos(phi) sin(phi); 0 -sin(phi) cos(phi)];
            Ry = [cos(theta) 0 -sin(theta); 0 1 0; sin(theta) 0 cos(theta)];
            Bl = Ry * Rx * Bb;   % frame with x,y ~ forward, left
            % 3) Heading solution: expected horizontal field for yaw psi is
            %    Fh*[cos(psi-dec), -sin(psi-dec)] in (forward, left), so
            %    psi = dec - atan2(Bl_left, Bl_forward).
            dec = obj.magDeclinationRad();
            psi = wrapPi(dec - atan2(Bl(2), Bl(1)));
            % 4) Circular mean (converges ~1/sqrt(n), robust to wrap).
            obj.magSum = obj.magSum + exp(1i * psi);
            obj.nMag = obj.nMag + 1;
            yawEst = wrapPi(angle(obj.magSum));
        end

    function dec = magDeclinationRad(obj)
        dec = deg2rad(obj.cfg.Align.magDeclinationDeg);
    end
end
end
