classdef GNSSModel < handle
%GNSSMODEL Synthetic GNSS receiver with rate, noise, bias, scheduled and
% random dropouts, outliers and measurement delay.
%
% [hasMeas, z, evt] = update(obj, t, truth) is polled every engine step.
%   z.p, z.v : NED measurement
%   z.R, z.Rv: measurement covariance
%   evt      : '' | 'MEAS' | 'MEAS_OUTLIER' | 'DROPOUT'  (per GNSS epoch)
%
% One class serves any config section: GNSSModel() reads cfg.GNSS;
% GNSSModel('GNSS2') reads cfg.GNSS2 (dual-source aiding).
%
% Satellite geometry: with useSatGeometry = true the per-epoch noise
% sigmas come from a live sky view: N satellites at fixed elevations
% with azimuths rotating at a representative (accelerated) period.
% sigmaH = sig0 * HDOP, sigmaV = sig0 * VDOP, so the vertical advantage
% of geometry is a *live observable* instead of a fixed number.

properties
    cfg
    section = 'GNSS'   % config section name ('GNSS' | 'GNSS2')
    nextEpoch = 0
    queue = {}            % delayed measurement queue (FIFO of structs)
    lastZ = []
    ndx = 0
    windows = zeros(0,2)  % dropout windows [t1 t2; ...]
    lastRate = nan
    lastEnabled = false
    gmState = zeros(3,1)  % Gauss-Markov correlated error state [m]
    gmInit = false        % true after the state is drawn from N(0, gmSigma)
    lastGmT = 0           % wall time of the last GM advance [s]
    % satellite geometry (used when useSatGeometry)
    satPhase = zeros(1,0) % azimuth phase [rad]
    satEl = zeros(1,0)    % elevation [rad]
    lastHDOP = nan
    lastVDOP = nan
end

methods
    function obj = GNSSModel(sectionName)
        if nargin >= 1 && ~isempty(sectionName)
            obj.section = char(sectionName);
        end
    end

    function updateParams(obj, cfg, tNow)
        c = cfg.(obj.section);
        oldRate = obj.lastRate;
        oldEnabled = obj.lastEnabled;
        newWindows = obj.parseWindows(c.dropoutText); % validate before mutation
        obj.cfg = cfg;
        obj.windows = newWindows;
        obj.lastRate = max(c.rate, 1e-3);
        obj.lastEnabled = logical(c.enabled);

        if isfield(c, 'useSatGeometry') && c.useSatGeometry
            nSat = c.satCount;
            if numel(obj.satPhase) ~= nSat || obj.lastRate ~= c.rate
                idx = (0:nSat-1)';
                % deliberately asymmetric sky: uneven azimuths, individual
                % orbital rates and varied elevations, so HDOP/VDOP visibly
                % vary as the geometry evolves (a rigidly rotating sky would
                % give a constant DOP and hide the geometry effect).
                obj.satPhase = (2*pi/nSat) * idx + (mod(3*idx + 1, 7) - 3) * 0.15;
                obj.satOmega = (2*pi / c.satPeriod) * (1 + 0.25*mod(idx + 2, 6)/5);
                elSet = [15 60 25 70 18 50];
                obj.satEl = deg2rad(elSet(mod(idx, 6) + 1));
            end
        end

        if nargin >= 3
            if oldEnabled && ~obj.lastEnabled
                % Never deliver stale delayed measurements after re-enable.
                obj.queue = {};
            elseif ~oldEnabled && obj.lastEnabled
                obj.nextEpoch = tNow;  % immediate acquisition on re-enable
            elseif isfinite(oldRate) && abs(oldRate - obj.lastRate) > ...
                    10*eps(max([1, obj.lastRate]))
                % Reschedule both rate increases and decreases from now.
                obj.nextEpoch = tNow + 1.0 / obj.lastRate;
            end
        end
    end

    function reset(obj)
        obj.nextEpoch = 0;
        obj.queue = {};
        obj.lastZ = [];
        obj.ndx = 0;
        obj.gmState = zeros(3,1);
        obj.gmInit = false;
        obj.lastGmT = 0;
        obj.lastHDOP = nan;
        obj.lastVDOP = nan;
    end

    function w = parseWindows(~, txt)
        w = zeros(0,2)
        if isstring(txt) && isscalar(txt), txt = char(txt); end
        if ~ischar(txt), return; end
        if isempty(strtrim(txt)), return; end
        segs = strsplit(txt, ';');
        for i = 1:numel(segs)
            seg = strtrim(segs{i});
            if isempty(seg), continue; end
            v = sscanf(seg, '%f');
            numericForm = ~isempty(regexp(seg, ...
                '^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?[ \t]+[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$', 'once'));
            if numel(v) ~= 2 || ~numericForm || any(~isfinite(v)) || v(1) < 0 || v(2) < v(1)
                error('NavSim:InvalidDropoutWindows', ...
                    'Invalid GNSS dropout window "%s"; expected "start end" with 0 <= start <= end.', seg);
            end
            w(end+1, :) = [v(1) v(2)]; %#ok<AGROW>
        end
    end

    function tf = inDropout(obj, t)
        c = obj.cfg.(obj.section);
        tf = false;
        if c.useDropout
            for i = 1:size(obj.windows, 1)
                if t >= obj.windows(i,1) && t <= obj.windows(i,2)
                    tf = true; return;
                end
            end
        end
        if c.useDropout && c.randDropProb > 0
            if rand < c.randDropProb, tf = true; return; end
        end
    end

    function g = advanceGm(obj, t, c)
        %ADVANCEGM Stationary Gauss-Markov correlated error (multipath-like).
        % The state follows x' = exp(-dt/tau)*x + sigma*sqrt(1-exp(-2dt/tau))*w
        % and is drawn from the stationary distribution N(0, gmSigma) at the
        % first epoch.  Deliberately NOT reflected in R: modelling mismatch
        % (overconfident filter vs correlated reality) is the demonstration.
        if ~obj.gmInit
            obj.gmState = c.gmSigma * randn(3,1);
            obj.gmInit = true;
        else
            dt = max(t - obj.lastGmT, 0);
            phi = exp(-dt / c.gmTau);
            sig = c.gmSigma * sqrt(max(1 - phi^2, 0));
            obj.gmState = phi * obj.gmState + sig * randn(3,1);
        end
        obj.lastGmT = t;
        g = obj.gmState;
    end

    function [sH, sV] = epochSigmas(obj, t, c)
        % Per-epoch noise sigmas. Fixed config values, or live DOP from the
        % satellite geometry when useSatGeometry is on.
        sH = c.posSigmaH * double(c.useNoise);
        sV = c.posSigmaV * double(c.useNoise);
        if isfield(c, 'useSatGeometry') && c.useNoise && c.useSatGeometry
            % advance sky: one step per receiver epoch, per-satellite rates
            obj.satPhase = mod(obj.satPhase + obj.satOmega / c.rate, 2*pi);
            A = zeros(numel(obj.satPhase), 4);
            for i = 1:numel(obj.satPhase)
                az = obj.satPhase(i); el = obj.satEl(i);
                % unit vector from receiver to satellite, NED (down +)
                A(i,1) = 1;
                A(i,2) = cos(el)*cos(az);
                A(i,3) = cos(el)*sin(az);
                A(i,4) = -sin(el);
            end
            Ginv = inv(A' * A);
            obj.lastHDOP = sqrt(max(Ginv(2,2) + Ginv(3,3), 0));
            obj.lastVDOP = sqrt(max(Ginv(4,4), 0));
            sH = c.sig0 * obj.lastHDOP;
            sV = c.sig0 * obj.lastVDOP;
        end
    end

    function [hasMeas, z, evt] = update(obj, t, truth)
        hasMeas = false;  z = [];  evt = '';
        c = obj.cfg.(obj.section);
        if ~c.enabled, return; end

        % --- new measurement epoch? ---
        if t >= obj.nextEpoch - 1e-12
            rate = max(c.rate, 1e-3);
            obj.nextEpoch = obj.nextEpoch + 1.0 / rate;
            if obj.nextEpoch < t   % rate changed at runtime: resync schedule
                obj.nextEpoch = t + 1.0 / rate;
            end
            if obj.inDropout(t)
                evt = 'DROPOUT';
            else
                [sH, sV] = obj.epochSigmas(t, c);
                pmeas = truth.p + c.biasNed(:) + [sH*randn; sH*randn; sV*randn];
                if c.useGmNoise
                    pmeas = pmeas + obj.advanceGm(t, c);
                end
                isOut = false;
                if c.useOutlier && rand < c.outlierProb
                    pmeas = pmeas + c.outlierMag * (2*rand(3,1) - 1);
                    isOut = true;
                end
                zs.p  = pmeas;
                zs.R  = diag([max(sH,0.05)^2, max(sH,0.05)^2, max(sV,0.05)^2]);
                zs.outlier = isOut;
                zs.tMeas = t;                 % physical measurement epoch
                zs.tEmit = t + c.delay;       % receiver delivery epoch
                if isfield(c, 'useSatGeometry') && c.useSatGeometry
                    zs.hdop = obj.lastHDOP; zs.vdop = obj.lastVDOP;
                end
                zs.lla = truth.lla;
                zs.hasVel = c.enableVel;
                if c.enableVel
                    sVel = c.velSigma * double(c.useNoise);
                    zs.v  = truth.v + sVel * randn(3,1);
                    if isOut && c.outlierVelSigma > 0
                        zs.v = zs.v + c.outlierVelSigma * (2*rand(3,1) - 1);
                    end
                    zs.Rv = eye(3) * max(sVel, 0.01)^2;
                else
                    zs.v = []; zs.Rv = [];
                end
                obj.queue{end+1} = zs; %#ok<AGROW>
                if isOut, evt = 'MEAS_OUTLIER'; else, evt = 'MEAS'; end
            end
        end

        % --- deliver delayed measurements ---
        if ~isempty(obj.queue)
            zq = obj.queue{1};
            if zq.tEmit <= t + 1e-12
                obj.queue(1) = [];
                hasMeas = true;
                z = zq;
                obj.lastZ = zq;
                obj.ndx = obj.ndx + 1;
            end
        end
    end
end

end
