classdef NavLogger < handle
%NAVLOGGER Preallocated time-series storage for every pipeline stage.
% Provides MAT/CSV export; slices for live plotting.

properties
    maxN
    k = 0
    t
    dtArr
    truthP
    truthV
    truthE
    gyroT
    accT
    gyroM
    accM
    imuBg
    imuBa
    insP
    insV
    insE
    fusP
    fusV
    fusE
    calBg
    calBa
    gnssP
    gnssV
    gnssFlag     % 1=meas, 2=injected outlier, 3=NIS reject, 4=OOSM unavailable
    gnssTMeas    % physical measurement epoch (distinct from delivery row time)
    gnssOosm     % 1 when delivered out of sequence, 0 in sequence, NaN without delivery
    sigP
    sigV
    sigA         % filter 1-sigma pos/vel/att
    innovN
    nis          % raw innovation NIS at latest aiding update
    gnssAccepted % 1 accepted, 0 rejected/unavailable, NaN without aided delivery
    oosmCount    % cumulative delayed measurements applied through this row
    alignEst     % alignment attitude estimate (NaN outside)
    refLla = zeros(3,1)
end

methods
    function obj = NavLogger(maxN, cfg)
        obj.maxN = maxN;
        z3 = nan(3, maxN);  z1 = nan(1, maxN);
        obj.t = z1; obj.dtArr = z1;
        obj.truthP = z3; obj.truthV = z3; obj.truthE = z3;
        obj.gyroT = z3; obj.accT = z3; obj.gyroM = z3; obj.accM = z3;
        obj.imuBg = z3; obj.imuBa = z3;
        obj.insP = z3; obj.insV = z3; obj.insE = z3;
        obj.fusP = z3; obj.fusV = z3; obj.fusE = z3;
        obj.calBg = z3; obj.calBa = z3;
        obj.gnssP = z3; obj.gnssV = z3; obj.gnssFlag = z1;
        obj.gnssTMeas = z1; obj.gnssOosm = z1;
        obj.sigP = z3; obj.sigV = z3; obj.sigA = z3;
        obj.innovN = z1; obj.nis = z1; obj.gnssAccepted = z1; obj.oosmCount = z1;
        obj.alignEst = z3; %#ok<*CPROPLC>
        obj.refLla = [cfg.INS.refLat; cfg.INS.refLon; cfg.INS.refH];
    end

    function growIfNeeded(obj, idx)
        if idx <= obj.maxN, return; end
        add = ceil(obj.maxN * 1.0);
        z3 = nan(3, add); z1 = nan(1, add);
        obj.t = [obj.t z1]; obj.dtArr = [obj.dtArr z1];
        for f = {'truthP','truthV','truthE','gyroT','accT','gyroM','accM', ...
                 'imuBg','imuBa','insP','insV','insE','fusP','fusV','fusE', ...
                 'calBg','calBa','gnssP','gnssV','sigP','sigV','sigA','alignEst'}
            fn = f{1};
            obj.(fn) = [obj.(fn) z3]; %#ok<AGROW>
        end
        obj.gnssFlag = [obj.gnssFlag z1]; obj.gnssTMeas = [obj.gnssTMeas z1];
        obj.gnssOosm = [obj.gnssOosm z1];
        obj.innovN = [obj.innovN z1]; obj.nis = [obj.nis z1];
        obj.gnssAccepted = [obj.gnssAccepted z1]; obj.oosmCount = [obj.oosmCount z1];
        obj.maxN = obj.maxN + add;
    end

    function logRow(obj, i, s)
        obj.growIfNeeded(i);
        obj.t(i) = s.t;          obj.dtArr(i) = s.dt;
        obj.truthP(:,i) = s.truthP;  obj.truthV(:,i) = s.truthV;  obj.truthE(:,i) = s.truthE;
        obj.gyroT(:,i) = s.gyroT;    obj.accT(:,i) = s.accT;
        obj.gyroM(:,i) = s.gyroM;    obj.accM(:,i) = s.accM;
        obj.imuBg(:,i) = s.imuBg;    obj.imuBa(:,i) = s.imuBa;
        obj.insP(:,i) = s.insP;      obj.insV(:,i) = s.insV;      obj.insE(:,i) = s.insE;
        obj.fusP(:,i) = s.fusP;      obj.fusV(:,i) = s.fusV;      obj.fusE(:,i) = s.fusE;
        obj.calBg(:,i) = s.calBg;    obj.calBa(:,i) = s.calBa;
        obj.gnssP(:,i) = s.gnssP;    obj.gnssV(:,i) = s.gnssV;    obj.gnssFlag(i) = s.gnssFlag;
        obj.gnssTMeas(i) = s.gnssTMeas; obj.gnssOosm(i) = s.gnssOosm;
        obj.sigP(:,i) = s.sigP;      obj.sigV(:,i) = s.sigV;      obj.sigA(:,i) = s.sigA;
        obj.innovN(i) = s.innovN; obj.nis(i) = s.nis;
        obj.gnssAccepted(i) = s.gnssAccepted; obj.oosmCount(i) = s.oosmCount;
        obj.alignEst(:,i) = s.alignEst;
        obj.k = max(obj.k, i);
    end

    function d = slice(obj)
        n = obj.k;
        grab = @(A) A(:, 1:n);
        d = struct();
        d.n = n;
        d.t = obj.t(1:n);       d.dt = obj.dtArr(1:n);
        d.truthP = grab(obj.truthP); d.truthV = grab(obj.truthV); d.truthE = grab(obj.truthE);
        d.gyroT = grab(obj.gyroT); d.accT = grab(obj.accT);
        d.gyroM = grab(obj.gyroM); d.accM = grab(obj.accM);
        d.imuBg = grab(obj.imuBg); d.imuBa = grab(obj.imuBa);
        d.insP = grab(obj.insP); d.insV = grab(obj.insV); d.insE = grab(obj.insE);
        d.fusP = grab(obj.fusP); d.fusV = grab(obj.fusV); d.fusE = grab(obj.fusE);
        d.calBg = grab(obj.calBg); d.calBa = grab(obj.calBa);
        d.gnssP = grab(obj.gnssP); d.gnssV = grab(obj.gnssV);
        d.gnssFlag = obj.gnssFlag(1:n); d.gnssTMeas = obj.gnssTMeas(1:n);
        d.gnssOosm = obj.gnssOosm(1:n);
        d.sigP = grab(obj.sigP); d.sigV = grab(obj.sigV); d.sigA = grab(obj.sigA);
        d.innovN = obj.innovN(1:n); d.nis = obj.nis(1:n);
        d.gnssAccepted = obj.gnssAccepted(1:n); d.oosmCount = obj.oosmCount(1:n);
        d.alignEst = grab(obj.alignEst);
        d.refLla = obj.refLla;
    end

    function saveMAT(obj, fname)
        d = obj.slice();
        save(fname, 'd');
    end

    function saveCSV(obj, fname)
        d = obj.slice();
        T = table(d.t(:), ...
            d.truthP(1,:).', d.truthP(2,:).', d.truthP(3,:).', ...
            d.truthV(1,:).', d.truthV(2,:).', d.truthV(3,:).', ...
            rad2deg(d.truthE(1,:).'), rad2deg(d.truthE(2,:).'), rad2deg(d.truthE(3,:).'), ...
            d.insP(1,:).', d.insP(2,:).', d.insP(3,:).', ...
            d.fusP(1,:).', d.fusP(2,:).', d.fusP(3,:).', ...
            d.gnssP(1,:).', d.gnssP(2,:).', d.gnssP(3,:).', ...
            d.gnssTMeas(:), d.gnssOosm(:), d.gnssFlag(:), d.nis(:), ...
            d.gnssAccepted(:), d.oosmCount(:), ...
            'VariableNames', {'t','truthN','truthE','truthD','vN','vE','vD', ...
              'rollDeg','pitchDeg','yawDeg','insN','insE','insD', ...
              'fusN','fusE','fusD','gnssN','gnssE','gnssD', ...
              'gnssTMeas','gnssOosm','gnssFlag','rawNIS','gnssAccepted','oosmCount'});
        writetable(T, fname);
    end
end
end
