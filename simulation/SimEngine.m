classdef SimEngine < handle
%SIMENGINE Orchestrates the full navigation data flow, step by step:
%   Trajectory -> Truth -> IMU -> Calibration -> INS -> (Prediction)
%               -> GNSS -> Fusion -> Navigation estimate -> Error analysis
% The engine is graphics-free so it can run headless (tests, experiments).

properties
    cfg
    traj
    imu
    gnss
    ins
    insPure           % free-running INS, never corrected by the filter
    align
    ekf
    log
    t = 0
    k = 0                 % logged rows
    istep = 0             % step counter
    phase = 'idle'        % 'idle' | 'align' | 'nav' | 'done'
    calibBg = zeros(3,1)  % online-estimated gyro bias correction
    calibBa = zeros(3,1)  % online-estimated accel bias correction
    refLla = zeros(3,1)
    lastGnssP = nan(3,1)
    lastGnssV = nan(3,1)
    gnssEvent = ''        % last GNSS epoch event: '', 'MEAS', 'MEAS_OUTLIER', 'DROPOUT'
    lastSnap = struct()
    maxN = 1000
    done = false
end

methods
    function obj = SimEngine(cfg)
        obj.configure(cfg);
    end

    function configure(obj, cfg)
        cfg = validateConfig(cfg);
        obj.cfg = cfg;
        cfg.Traj.durationVal = cfg.Sim.duration;   % used by 'Turn'
        obj.traj  = TrajectoryLibrary.make(cfg.Traj.type, cfg.Traj);
        obj.imu   = IMUModel();   obj.imu.updateParams(cfg);
        obj.gnss  = GNSSModel();  obj.gnss.updateParams(cfg);
        obj.ins   = INSMechanization();
        obj.insPure = INSMechanization();
        obj.align = Alignment();
        obj.ekf   = LooselyCoupledEKF();
        obj.refLla = [cfg.INS.refLat; cfg.INS.refLon; cfg.INS.refH];
        switch cfg.Sim.variableDt
            case 'jitter'
                dtMin = cfg.Sim.dt * max(0.2, 1 - cfg.Sim.dtJitter);
            otherwise
                dtMin = cfg.Sim.dt;
        end
        obj.maxN = ceil(cfg.Sim.duration / dtMin) + 1000;
        obj.log = NavLogger(obj.maxN, cfg);
        obj.resetState();
    end

    function applyRuntime(obj, cfg)
        % Hot-update of run-time editable parameters.
        cfg = validateConfig(cfg);
        oldMode = obj.cfg.Fusion.mode;
        % Only copy sections explicitly documented as runtime-safe.  The UI
        % may also contain pending Trajectory/Sim/INS/Align edits; copying the
        % whole struct here would apply those accidentally on the next IMU edit.
        runtimeCfg = obj.cfg;
        runtimeCfg.IMU = cfg.IMU;
        runtimeCfg.GNSS = cfg.GNSS;
        fusionRuntime = {'mode','useVel','qa','qg','qbg','qba','qScale','rScale'};
        for i = 1:numel(fusionRuntime)
            f = fusionRuntime{i};
            runtimeCfg.Fusion.(f) = cfg.Fusion.(f);
        end
        obj.gnss.updateParams(runtimeCfg, obj.t); % validate windows before mutation
        obj.imu.updateParams(runtimeCfg);
        obj.cfg = runtimeCfg;

        % A paused INS-only filter has stale covariance.  Reinitialize it
        % whenever aiding is enabled, and make INS-only mode truly unaided.
        if ~strcmp(oldMode, runtimeCfg.Fusion.mode)
            if strcmp(runtimeCfg.Fusion.mode, 'loose')
                obj.ekf.initState(runtimeCfg);
            else
                obj.ins.reset(obj.insPure.p, obj.insPure.v, obj.insPure.eul(), runtimeCfg);
                obj.calibBg = zeros(3,1);
                obj.calibBa = zeros(3,1);
                obj.ekf.initialized = false;
            end
        end
    end

    function resetState(obj)
        rng(obj.cfg.Sim.seed, 'twister');
        obj.imu.reset();
        obj.gnss.reset();
        obj.t = 0; obj.k = 0; obj.istep = 0;
        obj.done = false;
        obj.calibBg = zeros(3,1);  obj.calibBa = zeros(3,1);
        obj.lastGnssP = nan(3,1);  obj.lastGnssV = nan(3,1);
        obj.gnssEvent = '';
        obj.log = NavLogger(obj.maxN, obj.cfg);
        truth0 = obj.traj.fh(0);
        obj.align.reset(obj.cfg, truth0);
        obj.ekf.initialized = false;
        if obj.align.active
            obj.phase = 'align';
        else
            obj.phase = 'nav';
            obj.initNav(truth0);
        end
    end

    function initNav(obj, truthNow)
        eul0 = obj.align.finalize();
        p0 = truthNow.p(:) + obj.cfg.INS.initPosErr(:);
        v0 = truthNow.v(:) + obj.cfg.INS.initVelErr(:);
        obj.ins.reset(p0, v0, eul0, obj.cfg);
        obj.insPure.reset(p0, v0, eul0, obj.cfg);   % same initial estimate
        if strcmp(obj.cfg.Fusion.mode, 'loose')
            obj.ekf.initState(obj.cfg);
        end
    end

    function dtS = pickDt(obj)
        c = obj.cfg.Sim;
        switch c.variableDt
            case 'jitter'
                dtS = c.dt * max(0.2, 1 + c.dtJitter * (2*rand - 1));
            case 'tworate'
                if mod(obj.istep, 20) < 10
                    dtS = c.dt;
                else
                    dtS = c.dt * 4;
                end
            otherwise
                dtS = c.dt;
        end
    end

    function fusionOn = isFusionOn(obj)
        fusionOn = strcmp(obj.cfg.Fusion.mode, 'loose');
    end

    function step(obj)
        if obj.done, return; end
        c = obj.cfg;
        remaining = c.Sim.duration - obj.t;
        if remaining <= 1e-10*max(1, c.Sim.duration)
            obj.t = c.Sim.duration;
            obj.done = true;
            obj.phase = 'done';
            return;
        end
        dt = min(obj.pickDt(), remaining);  % never integrate beyond the requested duration
        obj.istep = obj.istep + 1;

        % ---------- Stage 1+2: Trajectory / Truth ----------
        truth = obj.traj.fh(obj.t);
        g = localGravity(c, -truth.p(3));
        gn = [0; 0; g];
        Ct = eul2dcm(truth.eul);
        wTrue = eulRates2body(truth.eul, truth.eulDot);
        fTrue = Ct' * (truth.a - gn);

        % ---------- Stage 3: IMU measurement ----------
        [wm, fm, dbg] = obj.imu.measure(wTrue, fTrue, dt);

        % ---------- GNSS runs every step (may produce a measurement) ---
        [hasG, z, evt] = obj.gnss.update(obj.t, truth);
        if ~isempty(evt), obj.gnssEvent = evt; end
        if hasG
            obj.lastGnssP = z.p;
            if z.hasVel, obj.lastGnssV = z.v; end
        end

        % Alignment owns samples t < duration.  Initialize navigation at
        % the first actual sample at/after the boundary, not one sample
        % earlier; otherwise every post-alignment state lags Truth by dt.
        if strcmp(obj.phase, 'align') && ...
                (obj.t - obj.align.t0) >= c.Align.duration - 1e-10*max(1, c.Align.duration)
            % Refresh transfer/static alignment at this boundary sample so
            % finalize() represents the same truth epoch used by initNav.
            obj.align.update(fm, truth);
            obj.phase = 'nav';
            obj.initNav(truth);
        end

        sRow = obj.emptyRow(obj.t, dt, truth, wTrue, fTrue, wm, fm, dbg);
        if hasG   % log GNSS in every phase (also during alignment)
            sRow.gnssP = z.p;  sRow.gnssFlag = 1 + double(z.outlier);
            if z.hasVel, sRow.gnssV = z.v; end
        end

        if strcmp(obj.phase, 'align')
            % ---------- Stage: Alignment ----------
            obj.align.update(fm, truth);
            sRow.alignEst = obj.align.estEul;
        else
            % ---------- Stage 7+8: GNSS update / Fusion ------------------
            % Measurement update acts on the state AT time t.
            if hasG && obj.isFusionOn()
                if ~obj.ekf.initialized, obj.ekf.initState(c); end
                obj.ekf.updatePos(z.p - obj.ins.p, z.R);
                if z.hasVel && c.Fusion.useVel
                    obj.ekf.updateVel(z.v - obj.ins.v, z.Rv);
                end
                dx = obj.ekf.consumeDx();
                obj.ins.correctState(dx(1:3), dx(4:6), dx(7:9));
                obj.calibBg = obj.calibBg + dx(10:12);
                obj.calibBa = obj.calibBa + dx(13:15);
            end

            % ---------- Log state at exactly t (aligned with truth) -----
            % INS trace = free-running pure INS (no filter corrections);
            % Fused trace = feedback-corrected INS.
            sRow.insP = obj.insPure.p;  sRow.insV = obj.insPure.v;  sRow.insE = obj.insPure.eul();
            sRow.fusP = obj.ins.p;  sRow.fusV = obj.ins.v;  sRow.fusE = obj.ins.eul();
            sRow.calBg = obj.calibBg;  sRow.calBa = obj.calibBa;
            if obj.ekf.initialized
                sg = obj.ekf.sigmas();
                sRow.sigP = sg(1:3);  sRow.sigV = sg(4:6);  sRow.sigA = sg(7:9);
                sRow.innovN = norm(obj.ekf.lastInnov);
            end
        end

        % ---------- Stage 9: Log/snapshot, all consistently at t -------
        obj.k = obj.k + 1;
        obj.log.logRow(obj.k, sRow);
        obj.lastSnap = obj.buildSnapshot(sRow, truth, wTrue, fTrue, wm, fm, dbg, hasG);

        if strcmp(obj.phase, 'nav')
            % Recompute calibration after the measurement update so a new
            % bias estimate is effective in this very propagation interval.
            wc = wm - obj.calibBg;
            fc = fm - obj.calibBa;
            gIns = localGravity(c, -obj.ins.p(3));
            gPure = localGravity(c, -obj.insPure.p(3));
            obj.ins.step(wc, fc, dt, gIns);
            obj.insPure.step(wm, fm, dt, gPure);
            if obj.isFusionOn()
                obj.ekf.predict(obj.ins.C, fc, dt, c);
            end
        end

        obj.t = obj.t + dt;
        if obj.t >= c.Sim.duration - 1e-10*max(1, c.Sim.duration)
            obj.t = c.Sim.duration;
            obj.done = true;
            obj.phase = 'done';
        end
    end

    function runToEnd(obj, cb)
        n = 0;
        while ~obj.done
            obj.step();
            n = n + 1;
            if nargin >= 2 && ~isempty(cb) && mod(n, 2000) == 0
                cb(obj);
            end
        end
    end

    function d = results(obj)
        d = obj.log.slice();
        d.errPosIns = sqrt(sum((d.insP - d.truthP).^2, 1));
        d.errPosFus = sqrt(sum((d.fusP - d.truthP).^2, 1));
        d.errVelIns = sqrt(sum((d.insV - d.truthV).^2, 1));
        d.errVelFus = sqrt(sum((d.fusV - d.truthV).^2, 1));
        d.errAttIns = sqrt(sum(wrapPi(d.insE - d.truthE).^2, 1));
        d.errAttFus = sqrt(sum(wrapPi(d.fusE - d.truthE).^2, 1));
        d.cfg = obj.cfg;
    end

    function pts = sampleTruth(obj, n)
        ts = linspace(0, obj.cfg.Sim.duration, n);
        pts = zeros(3, n);
        for i = 1:n
            th = obj.traj.fh(ts(i));
            pts(:, i) = th.p;
        end
    end

    function snap = getSnapshot(obj)
        snap = obj.lastSnap;
        if ~isfield(snap, 'phase')
            snap.phase = obj.phase;
            snap.t = obj.t;
        end
        snap.engineTime = obj.t;
        snap.done = obj.done;
    end
end

methods (Access = private)
    function sRow = emptyRow(obj, t, dt, truth, wT, fT, wm, fm, dbg)
        sRow = struct();
        sRow.t = t;  sRow.dt = dt;
        sRow.truthP = truth.p; sRow.truthV = truth.v; sRow.truthE = truth.eul;
        sRow.gyroT = wT; sRow.accT = fT;
        sRow.gyroM = wm; sRow.accM = fm;
        sRow.imuBg = dbg.bg; sRow.imuBa = dbg.ba;
        if strcmp(obj.phase, 'nav')
            sRow.insP = obj.ins.p; sRow.insV = obj.ins.v; sRow.insE = obj.ins.eul();
            sRow.fusP = obj.ins.p; sRow.fusV = obj.ins.v; sRow.fusE = obj.ins.eul();
        else
            sRow.insP = nan(3,1); sRow.insV = nan(3,1); sRow.insE = nan(3,1);
            sRow.fusP = nan(3,1); sRow.fusV = nan(3,1); sRow.fusE = nan(3,1);
        end
        sRow.calBg = obj.calibBg; sRow.calBa = obj.calibBa;
        sRow.gnssP = nan(3,1); sRow.gnssV = nan(3,1); sRow.gnssFlag = nan;
        sRow.sigP = nan(3,1); sRow.sigV = nan(3,1); sRow.sigA = nan(3,1);
        sRow.innovN = nan;
        sRow.alignEst = nan(3,1);
    end

    function snap = buildSnapshot(obj, sRow, truth, wT, fT, wm, fm, dbg, hasG)
        snap = struct();
        snap.phase = obj.phase;
        snap.truth = struct('p', truth.p, 'v', truth.v, 'eul', truth.eul, ...
            'lla', ned2lla(truth.p, obj.refLla));
        snap.imu = struct('w', wm, 'f', fm, 'wTrue', wT, 'fTrue', fT, ...
            'bg', dbg.bg, 'ba', dbg.ba);
        snap.calib = struct('w', wm - obj.calibBg, 'f', fm - obj.calibBa, ...
            'bgEst', obj.calibBg, 'baEst', obj.calibBa);
        snap.insState = struct('p', sRow.insP, 'v', sRow.insV, ...
            'eul', sRow.insE, 'lla', ned2lla(sRow.insP, obj.refLla));
        snap.gnss = struct('has', hasG, 'p', obj.lastGnssP, 'v', obj.lastGnssV, ...
            'event', obj.gnssEvent, 'enabled', obj.cfg.GNSS.enabled);
        if obj.ekf.initialized
            sg = obj.ekf.sigmas();
            snap.pred = struct('sigP', sg(1:3), 'sigV', sg(4:6), 'sigA', sg(7:9), ...
                'innov', obj.ekf.lastInnov, 'nis', obj.ekf.lastNIS);
        else
            snap.pred = struct('sigP', nan(3,1), 'sigV', nan(3,1), 'sigA', nan(3,1), ...
                'innov', nan(3,1), 'nis', nan);
        end
        snap.fused = struct('p', sRow.fusP, 'v', sRow.fusV, 'eul', sRow.fusE, ...
            'lla', ned2lla(sRow.fusP, obj.refLla));
        snap.err = struct('posIns', norm(sRow.insP - truth.p), ...
            'posFus', norm(sRow.fusP - truth.p), ...
            'attInsDeg', rad2deg(norm(wrapPi(sRow.insE - truth.eul))), ...
            'attFusDeg', rad2deg(norm(wrapPi(sRow.fusE - truth.eul))), ...
            'velFus', norm(sRow.fusV - truth.v));
        snap.align = struct('active', strcmp(obj.phase,'align'), ...
            'est', obj.align.estEul, 'n', obj.align.n);
        snap.dt = sRow.dt;
    end
end
end
