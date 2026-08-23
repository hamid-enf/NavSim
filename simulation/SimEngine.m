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
    stateHistory = {}       % fixed-lag prior/post states and IMU intervals for OOSM
    oosmApplied = 0
    oosmRejected = 0
    oosmTooOld = 0
    gnssRejected = 0
    lastMeasDiag = struct()
    maxN = 1000
    done = false
end

methods
    function obj = SimEngine(cfg)
        obj.configure(cfg);
    end

    function configure(obj, cfg)
        cfg = validateConfig(cfg);

        % Build/validate every replacement locally first.  If a user-defined
        % trajectory or GNSS window is invalid, the currently running engine
        % remains intact instead of being left half-configured.
        trajCfg = cfg.Traj;
        trajCfg.durationVal = cfg.Sim.duration;   % used by 'Turn'
        newTraj = TrajectoryLibrary.make(cfg.Traj.type, trajCfg);
        newImu = IMUModel();   newImu.updateParams(cfg);
        newGnss = GNSSModel(); newGnss.updateParams(cfg);
        newIns = INSMechanization();
        newInsPure = INSMechanization();
        newAlign = Alignment();
        newEkf = LooselyCoupledEKF();
        switch cfg.Sim.variableDt
            case 'jitter'
                dtMin = cfg.Sim.dt * max(0.2, 1 - cfg.Sim.dtJitter);
            otherwise
                dtMin = cfg.Sim.dt;
        end
        newMaxN = ceil(cfg.Sim.duration / dtMin) + 1000;

        obj.cfg = cfg;
        obj.traj = newTraj;
        obj.imu = newImu;
        obj.gnss = newGnss;
        obj.ins = newIns;
        obj.insPure = newInsPure;
        obj.align = newAlign;
        obj.ekf = newEkf;
        obj.refLla = [cfg.INS.refLat; cfg.INS.refLon; cfg.INS.refH];
        obj.maxN = newMaxN;
        obj.resetState();
    end

    function applyRuntime(obj, cfg)
        % Hot-update of run-time editable parameters.
        oldMode = obj.cfg.Fusion.mode;
        oldUseOOSM = obj.cfg.Fusion.useOOSM;
        % Only copy sections explicitly documented as runtime-safe.  The UI
        % may also contain pending Trajectory/Sim/INS/Align edits; copying the
        % whole struct here would apply those accidentally on the next IMU edit.
        runtimeCfg = obj.cfg;
        runtimeCfg.IMU = cfg.IMU;
        runtimeCfg.GNSS = cfg.GNSS;
        fusionRuntime = {'mode','useVel','qa','qg','qbg','qba','qScale','rScale', ...
            'robustMode','nisGatePos','nisGateVel','maxRInflation','useOOSM','oosmLag'};
        for i = 1:numel(fusionRuntime)
            f = fusionRuntime{i};
            runtimeCfg.Fusion.(f) = cfg.Fusion.(f);
        end
        % Validate the merged config, not unrelated pending structural edits
        % in the UI candidate.
        runtimeCfg = validateConfig(runtimeCfg);
        obj.gnss.updateParams(runtimeCfg, obj.t); % validate windows before mutation
        obj.imu.updateParams(runtimeCfg);
        obj.cfg = runtimeCfg;
        if oldUseOOSM ~= runtimeCfg.Fusion.useOOSM
            % History starts at the toggle epoch; never reuse a partial
            % window collected under a different delayed-update policy.
            obj.stateHistory = {};
        end

        % A paused INS-only filter has stale covariance.  Reinitialize it
        % whenever aiding is enabled, and make INS-only mode truly unaided.
        if ~strcmp(oldMode, runtimeCfg.Fusion.mode)
            obj.stateHistory = {}; % covariance model changed; old lag states are invalid
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
        obj.lastSnap = struct();
        obj.stateHistory = {};
        obj.oosmApplied = 0; obj.oosmRejected = 0; obj.oosmTooOld = 0;
        obj.gnssRejected = 0;
        obj.lastMeasDiag = struct('innov',zeros(3,1),'nis',0,'rawNIS',0, ...
            'gate',inf,'accepted',true,'posAccepted',true,'velAccepted',true);
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

        % ---------- Stage 1+2: Trajectory / WGS84 truth ----------
        rawTruth = obj.traj.fh(obj.t);
        if strcmp(c.INS.earthModel, 'wgs84')
            truth = earthTruth(rawTruth, c, obj.refLla);
            wTrue = truth.wIb; fTrue = truth.fB;
        else
            truth = rawTruth;
            truth.lla = ned2lla(truth.p, obj.refLla);
            truth.C = eul2dcm(truth.eul);
            truth.wie = zeros(3,1); truth.wen = zeros(3,1);
            g = localGravity(c, -truth.p(3), truth.lla(1));
            wTrue = eulRates2body(truth.eul, truth.eulDot);
            fTrue = truth.C' * (truth.a - [0;0;g]);
            truth.wIb = wTrue; truth.fB = fTrue;
        end

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

        if strcmp(obj.phase,'nav') && obj.isFusionOn() && c.Fusion.useOOSM
            obj.appendHistory(obj.t);
        end

        sRow = obj.emptyRow(obj.t, dt, truth, wTrue, fTrue, wm, fm, dbg);
        if hasG   % log GNSS in every phase (also during alignment)
            sRow.gnssP = z.p;  sRow.gnssFlag = 1 + double(z.outlier);
            sRow.gnssTMeas = z.tMeas;
            sRow.gnssOosm = double(z.tMeas < obj.t-1e-10);
            if z.hasVel, sRow.gnssV = z.v; end
        end

        if strcmp(obj.phase, 'align')
            % ---------- Stage: Alignment ----------
            obj.align.update(fm, truth);
            sRow.alignEst = obj.align.estEul;
        else
            % ---------- Stage 7+8: robust current/OOSM GNSS update ------
            if hasG && obj.isFusionOn()
                if ~obj.ekf.initialized, obj.ekf.initState(c); end
                isDelayed = isfield(z,'tMeas') && z.tMeas < obj.t-1e-10;
                if isDelayed && c.Fusion.useOOSM
                    [accepted,measDiag] = obj.applyOOSM(z);
                else
                    [accepted,measDiag] = obj.applyMeasurement(z);
                    if accepted, obj.addHistoryMeasurement(z); end
                    obj.updateLatestHistoryPost();
                end
                obj.lastMeasDiag = measDiag;
                if ~accepted
                    if strcmp(measDiag.reason,'nis')
                        obj.gnssRejected = obj.gnssRejected + 1;
                        sRow.gnssFlag = 3; obj.gnssEvent = 'REJECTED_NIS';
                    else
                        sRow.gnssFlag = 4; obj.gnssEvent = upper(['OOSM_' measDiag.reason]);
                    end
                elseif isDelayed && c.Fusion.useOOSM
                    obj.gnssEvent = 'OOSM_APPLIED';
                elseif isDelayed
                    obj.gnssEvent = 'DELAY_APPLIED_CURRENT';
                end
            else
                obj.updateLatestHistoryPost();
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
                if hasG && obj.isFusionOn()
                    sRow.nis = obj.lastMeasDiag.rawNIS;
                    sRow.gnssAccepted = double(obj.lastMeasDiag.accepted);
                end
                sRow.oosmCount = obj.oosmApplied;
            end
        end

        % ---------- Stage 9: Log/snapshot, all consistently at t -------
        obj.k = obj.k + 1;
        obj.log.logRow(obj.k, sRow);
        obj.lastSnap = obj.buildSnapshot(sRow, truth, wTrue, fTrue, wm, fm, dbg, hasG);

        if strcmp(obj.phase, 'nav')
            % Store the exact raw increment/config so a delayed measurement
            % can rewind and deterministically repropagate this interval.
            obj.recordHistoryInterval(wm,fm,dt,c);
            wc = wm-obj.calibBg; fc = fm-obj.calibBa;
            obj.ins.step(wc,fc,dt,c);
            obj.insPure.step(wm,fm,dt,c);
            if obj.isFusionOn()
                obj.ekf.predict(obj.ins.C,fc,dt,c,obj.ins.lla,obj.ins.v);
            end
        end

        obj.t = obj.t + dt;
        obj.trimHistory();
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
    function appendHistory(obj,t)
        e=struct('t',t,'prior',obj.captureFusedState(),'post',obj.captureFusedState(), ...
            'measurements',{{}},'wm',[],'fm',[],'dt',0,'cfg',[]);
        obj.stateHistory{end+1}=e;
    end

    function s=captureFusedState(obj)
        s=struct('ins',obj.ins.getState(),'ekf',obj.ekf.getState(), ...
            'calibBg',obj.calibBg,'calibBa',obj.calibBa);
    end

    function restoreFusedState(obj,s)
        obj.ins.setState(s.ins); obj.ekf.setState(s.ekf);
        obj.calibBg=s.calibBg; obj.calibBa=s.calibBa;
    end

    function updateLatestHistoryPost(obj)
        if isempty(obj.stateHistory), return; end
        e=obj.stateHistory{end}; e.post=obj.captureFusedState(); obj.stateHistory{end}=e;
    end

    function addHistoryMeasurement(obj,z)
        if isempty(obj.stateHistory), return; end
        rec=struct('z',z,'cfg',obj.cfg);
        e=obj.stateHistory{end}; e.measurements{end+1}=rec; obj.stateHistory{end}=e;
    end

    function recordHistoryInterval(obj,wm,fm,dt,cfg)
        if isempty(obj.stateHistory), return; end
        e=obj.stateHistory{end}; e.wm=wm; e.fm=fm; e.dt=dt; e.cfg=cfg;
        e.post=obj.captureFusedState(); obj.stateHistory{end}=e;
    end

    function [accepted,d]=applyMeasurement(obj,z,cfgMeas)
        if nargin<3, cfgMeas=obj.cfg; end
        obj.ekf.updateParams(cfgMeas);
        posOK=obj.ekf.updatePos(z.p-obj.ins.p,z.R);
        d=struct('innov',obj.ekf.lastInnov,'nis',obj.ekf.lastNIS, ...
            'rawNIS',obj.ekf.lastRawNIS,'gate',obj.ekf.lastGate, ...
            'accepted',false,'posAccepted',posOK,'velAccepted',true,'reason','nis');
        velOK=false; useVel=z.hasVel && cfgMeas.Fusion.useVel;
        if useVel
            vMeas=z.v;
            if strcmp(cfgMeas.INS.earthModel,'wgs84') && isfield(z,'lla') && ~isempty(z.lla)
                vMeas=nedRotation(obj.ins.lla)*nedRotation(z.lla)'*vMeas;
            end
            velOK=obj.ekf.updateVel(vMeas-obj.ins.v,z.Rv);
            d.velAccepted=velOK;
        end
        accepted=posOK || (useVel && velOK); d.accepted=accepted;
        if accepted, d.reason='accepted'; end
        if accepted
            dx=obj.ekf.consumeDx();
            obj.ins.correctState(dx(1:3),dx(4:6),dx(7:9));
            obj.calibBg=obj.calibBg+dx(10:12);
            obj.calibBa=obj.calibBa+dx(13:15);
        end
    end

    function [accepted,d]=applyOOSM(obj,z)
        accepted=false;
        d=struct('innov',zeros(3,1),'nis',nan,'rawNIS',nan,'gate',nan, ...
            'accepted',false,'posAccepted',false,'velAccepted',false,'reason','too_old');
        if isempty(obj.stateHistory), obj.oosmTooOld=obj.oosmTooOld+1; return; end
        times=cellfun(@(h) h.t,obj.stateHistory);
        [err,idx]=min(abs(times-z.tMeas));
        tol=1e-8*max(1,abs(z.tMeas));
        if err>tol || obj.t-z.tMeas>obj.cfg.Fusion.oosmLag+tol
            obj.oosmTooOld=obj.oosmTooOld+1; return;
        end
        current=obj.captureFusedState(); historyBefore=obj.stateHistory;
        % Gate the new sample against the fully corrected historical epoch.
        obj.restoreFusedState(obj.stateHistory{idx}.post);
        [accepted,d]=obj.applyMeasurement(z);
        obj.restoreFusedState(current);
        if ~accepted
            obj.oosmRejected=obj.oosmRejected+1; return;
        end
        e=obj.stateHistory{idx};
        e.measurements{end+1}=struct('z',z,'cfg',obj.cfg); obj.stateHistory{idx}=e;
        % Rebuild every state in the lag window from the historical prior.
        obj.restoreFusedState(e.prior);
        for j=idx:numel(obj.stateHistory)
            hj=obj.stateHistory{j};
            if j>idx
                hj.prior=obj.captureFusedState();
            end
            for m=1:numel(hj.measurements)
                rec=hj.measurements{m};
                obj.applyMeasurement(rec.z,rec.cfg);
            end
            hj.post=obj.captureFusedState(); obj.stateHistory{j}=hj;
            if j<numel(obj.stateHistory)
                if isempty(hj.wm) || hj.dt<=0
                    obj.restoreFusedState(current); obj.stateHistory=historyBefore;
                    obj.oosmRejected=obj.oosmRejected+1;
                    accepted=false; d.accepted=false; d.reason='replay'; return;
                end
                wc=hj.wm-obj.calibBg; fc=hj.fm-obj.calibBa;
                obj.ins.step(wc,fc,hj.dt,hj.cfg);
                obj.ekf.predict(obj.ins.C,fc,hj.dt,hj.cfg,obj.ins.lla,obj.ins.v);
            end
        end
        obj.ekf.updateParams(obj.cfg);
        eLast=obj.stateHistory{end}; eLast.post=obj.captureFusedState();
        obj.stateHistory{end}=eLast;
        obj.oosmApplied=obj.oosmApplied+1;
    end

    function trimHistory(obj)
        if isempty(obj.stateHistory), return; end
        cutoff=obj.t-obj.cfg.Fusion.oosmLag;
        while numel(obj.stateHistory)>1 && obj.stateHistory{2}.t<cutoff
            obj.stateHistory(1)=[];
        end
    end

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
        sRow.gnssTMeas = nan; sRow.gnssOosm = nan;
        sRow.sigP = nan(3,1); sRow.sigV = nan(3,1); sRow.sigA = nan(3,1);
        sRow.innovN = nan; sRow.nis = nan; sRow.gnssAccepted = nan;
        sRow.oosmCount = obj.oosmApplied;
        sRow.alignEst = nan(3,1);
    end

    function snap = buildSnapshot(obj, sRow, truth, wT, fT, wm, fm, dbg, hasG)
        snap = struct();
        snap.phase = obj.phase;
        % This timestamp identifies the state represented by every payload
        % below.  engineTime, added by getSnapshot(), is the next integration
        % boundary and is intentionally allowed to be one dt later.
        snap.t = sRow.t;
        snap.truth = struct('p',truth.p,'v',truth.v,'eul',truth.eul,'lla',truth.lla, ...
            'wie',truth.wie,'wen',truth.wen);
        snap.imu = struct('w', wm, 'f', fm, 'wTrue', wT, 'fTrue', fT, ...
            'bg', dbg.bg, 'ba', dbg.ba);
        snap.calib = struct('w', wm - obj.calibBg, 'f', fm - obj.calibBa, ...
            'bgEst', obj.calibBg, 'baEst', obj.calibBa);
        snap.insState = struct('p', sRow.insP, 'v', sRow.insV, ...
            'eul', sRow.insE, 'lla', ned2lla(sRow.insP, obj.refLla));
        snap.gnss = struct('has', hasG, 'p', obj.lastGnssP, 'v', obj.lastGnssV, ...
            'event', obj.gnssEvent, 'enabled', obj.cfg.GNSS.enabled, ...
            'tMeas',sRow.gnssTMeas,'oosm',sRow.gnssOosm);
        if obj.ekf.initialized
            sg = obj.ekf.sigmas();
            d=obj.lastMeasDiag;
            snap.pred = struct('sigP',sg(1:3),'sigV',sg(4:6),'sigA',sg(7:9), ...
                'innov',d.innov,'nis',d.nis,'rawNIS',d.rawNIS, ...
                'gate',d.gate,'accepted',d.accepted,'posAccepted',d.posAccepted, ...
                'velAccepted',d.velAccepted,'rejected',obj.gnssRejected, ...
                'oosmApplied',obj.oosmApplied,'oosmRejected',obj.oosmRejected, ...
                'oosmTooOld',obj.oosmTooOld);
        else
            snap.pred = struct('sigP',nan(3,1),'sigV',nan(3,1),'sigA',nan(3,1), ...
                'innov',nan(3,1),'nis',nan,'rawNIS',nan,'gate',nan,'accepted',false, ...
                'posAccepted',false,'velAccepted',false, ...
                'rejected',obj.gnssRejected,'oosmApplied',obj.oosmApplied, ...
                'oosmRejected',obj.oosmRejected,'oosmTooOld',obj.oosmTooOld);
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
